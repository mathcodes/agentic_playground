# Entity Framework Core Tips and Best Practices

## Table of Contents
1. [DbContext Configuration](#dbcontext-configuration)
2. [Query Optimization](#query-optimization)
3. [Change Tracking](#change-tracking)
4. [Loading Strategies](#loading-strategies)
5. [Migrations](#migrations)
6. [Transactions](#transactions)
7. [Performance Tips](#performance-tips)
8. [Common Pitfalls](#common-pitfalls)

## DbContext Configuration

### Basic DbContext Setup

```csharp
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<Customer> Customers { get; set; }
    public DbSet<Order> Orders { get; set; }
    public DbSet<Product> Products { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure entities
        modelBuilder.Entity<Customer>(entity =>
        {
            entity.ToTable("customers");
            entity.HasKey(e => e.CustomerId);
            
            entity.Property(e => e.Email)
                .IsRequired()
                .HasMaxLength(255);
            
            entity.HasIndex(e => e.Email).IsUnique();
        });

        // Configure relationships
        modelBuilder.Entity<Order>()
            .HasOne(o => o.Customer)
            .WithMany(c => c.Orders)
            .HasForeignKey(o => o.CustomerId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
```

### Connection String Configuration

```csharp
// In Program.cs or Startup.cs
builder.Services.AddDbContext<ApplicationDbContext>(options =>
{
    options.UseNpgsql(
        builder.Configuration.GetConnectionString("DefaultConnection"),
        npgsqlOptions =>
        {
            npgsqlOptions.CommandTimeout(30);
            npgsqlOptions.EnableRetryOnFailure(
                maxRetryCount: 3,
                maxRetryDelay: TimeSpan.FromSeconds(5),
                errorCodesToAdd: null
            );
        }
    );

    // Enable sensitive data logging in development only
    if (builder.Environment.IsDevelopment())
    {
        options.EnableSensitiveDataLogging();
        options.EnableDetailedErrors();
    }

    // Log SQL queries
    options.LogTo(Console.WriteLine, LogLevel.Information);
});
```

### DbContext Lifetime Management

```csharp
// Good: Use dependency injection (scoped lifetime)
public class CustomerController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public CustomerController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Customer>> GetCustomer(int id)
    {
        var customer = await _context.Customers.FindAsync(id);
        return customer == null ? NotFound() : Ok(customer);
    }
}

// Bad: Creating DbContext manually in every method
public class BadCustomerService
{
    public Customer GetCustomer(int id)
    {
        using var context = new ApplicationDbContext();  // Don't do this!
        return context.Customers.Find(id);
    }
}
```

## Query Optimization

### Select Only What You Need

```csharp
// Bad: Loading entire entity when only need few properties
var customers = await context.Customers
    .Where(c => c.Country == "USA")
    .ToListAsync();
var names = customers.Select(c => c.Name);

// Good: Project to anonymous type or DTO
var customerNames = await context.Customers
    .Where(c => c.Country == "USA")
    .Select(c => new { c.CustomerId, c.Name, c.Email })
    .ToListAsync();

// Better: Project to specific DTO
public class CustomerSummaryDto
{
    public int CustomerId { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}

var customerDtos = await context.Customers
    .Where(c => c.Country == "USA")
    .Select(c => new CustomerSummaryDto
    {
        CustomerId = c.CustomerId,
        Name = c.Name,
        Email = c.Email
    })
    .ToListAsync();
```

### Use AsNoTracking for Read-Only Queries

```csharp
// When you only need to read data (not update)
var products = await context.Products
    .AsNoTracking()  // 30-40% performance improvement
    .Where(p => p.CategoryId == 5)
    .ToListAsync();

// For all queries in a DbContext
public class ReadOnlyDbContext : ApplicationDbContext
{
    public ReadOnlyDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
        ChangeTracker.QueryTrackingBehavior = QueryTrackingBehavior.NoTracking;
    }
}
```

### Avoid N+1 Query Problem

```csharp
// Bad: N+1 queries (1 query for customers + N queries for orders)
var customers = await context.Customers.ToListAsync();
foreach (var customer in customers)
{
    // Each iteration executes a separate query!
    var orderCount = customer.Orders.Count();
}

// Good: Eager loading with Include
var customers = await context.Customers
    .Include(c => c.Orders)
    .ToListAsync();

// Better: Project to avoid loading unnecessary data
var customerOrderCounts = await context.Customers
    .Select(c => new
    {
        c.CustomerId,
        c.Name,
        OrderCount = c.Orders.Count()
    })
    .ToListAsync();
```

### Efficient Paging

```csharp
// Inefficient: Still loads all records before skipping
var page = await context.Products
    .OrderBy(p => p.ProductId)
    .Skip(pageNumber * pageSize)
    .Take(pageSize)
    .ToListAsync();

// More efficient for large datasets: Use keyset pagination
var lastProductId = 100;  // Last ID from previous page
var nextPage = await context.Products
    .Where(p => p.ProductId > lastProductId)
    .OrderBy(p => p.ProductId)
    .Take(pageSize)
    .ToListAsync();
```

### Compiled Queries

```csharp
// For frequently executed queries, compile them
private static readonly Func<ApplicationDbContext, int, Task<Customer>> GetCustomerById =
    EF.CompileAsyncQuery((ApplicationDbContext context, int id) =>
        context.Customers
            .Include(c => c.Orders)
            .FirstOrDefault(c => c.CustomerId == id)
    );

// Usage
var customer = await GetCustomerById(context, customerId);
```

## Change Tracking

### Understanding Change Tracking

```csharp
// Entity states
public async Task DemonstrateEntityStates()
{
    // Detached: Entity not tracked
    var customer = new Customer { Name = "John" };
    var state = context.Entry(customer).State;  // Detached

    // Added: Will be inserted
    context.Customers.Add(customer);
    state = context.Entry(customer).State;  // Added

    await context.SaveChangesAsync();
    state = context.Entry(customer).State;  // Unchanged

    // Modified: Will be updated
    customer.Email = "john@example.com";
    state = context.Entry(customer).State;  // Modified

    await context.SaveChangesAsync();
    state = context.Entry(customer).State;  // Unchanged

    // Deleted: Will be deleted
    context.Customers.Remove(customer);
    state = context.Entry(customer).State;  // Deleted

    await context.SaveChangesAsync();
    // Entity is now detached
}
```

### Detaching Entities

```csharp
// Detach entity to prevent tracking
var customer = await context.Customers.FindAsync(id);
context.Entry(customer).State = EntityState.Detached;

// Clear all tracked entities
context.ChangeTracker.Clear();
```

### Update Specific Properties

```csharp
// Only update specific properties
var customer = await context.Customers.FindAsync(id);
customer.Email = "newemail@example.com";
customer.Phone = "555-1234";

// Mark only specific properties as modified
context.Entry(customer).Property(c => c.Email).IsModified = true;
context.Entry(customer).Property(c => c.Phone).IsModified = true;

await context.SaveChangesAsync();

// Alternative: Attach and set state
var customer = new Customer { CustomerId = id };
context.Customers.Attach(customer);
customer.Email = "newemail@example.com";
context.Entry(customer).Property(c => c.Email).IsModified = true;
await context.SaveChangesAsync();
```

## Loading Strategies

### Eager Loading

```csharp
// Load related data immediately
var customers = await context.Customers
    .Include(c => c.Orders)
        .ThenInclude(o => o.OrderItems)
            .ThenInclude(oi => oi.Product)
    .Where(c => c.Country == "USA")
    .ToListAsync();

// Multiple includes
var orders = await context.Orders
    .Include(o => o.Customer)
    .Include(o => o.OrderItems)
    .ToListAsync();
```

### Explicit Loading

```csharp
// Load related data on demand
var customer = await context.Customers.FindAsync(id);

// Load orders separately
await context.Entry(customer)
    .Collection(c => c.Orders)
    .LoadAsync();

// Load filtered related data
await context.Entry(customer)
    .Collection(c => c.Orders)
    .Query()
    .Where(o => o.OrderDate >= DateTime.UtcNow.AddMonths(-1))
    .LoadAsync();
```

### Lazy Loading

```csharp
// Enable lazy loading (install Microsoft.EntityFrameworkCore.Proxies)
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseLazyLoadingProxies()
        .UseNpgsql(connectionString)
);

// Mark navigation properties as virtual
public class Customer
{
    public int CustomerId { get; set; }
    public string Name { get; set; }
    
    // Virtual enables lazy loading
    public virtual ICollection<Order> Orders { get; set; }
}

// Orders automatically loaded when accessed
var customer = await context.Customers.FindAsync(id);
var orderCount = customer.Orders.Count();  // Lazy loads orders
```

### Split Queries

```csharp
// When including multiple collections, use split queries
var customers = await context.Customers
    .Include(c => c.Orders)
    .Include(c => c.Addresses)
    .AsSplitQuery()  // Executes separate queries for each Include
    .ToListAsync();

// Make split queries default
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseNpgsql(connectionString)
        .UseQuerySplittingBehavior(QuerySplittingBehavior.SplitQuery)
);
```

## Migrations

### Creating Migrations

```bash
# Add new migration
dotnet ef migrations add InitialCreate

# Add migration with custom name
dotnet ef migrations add AddCustomerEmailIndex

# Update database
dotnet ef database update

# Rollback to specific migration
dotnet ef database update PreviousMigrationName

# Generate SQL script
dotnet ef migrations script

# Generate SQL script for specific range
dotnet ef migrations script FromMigration ToMigration
```

### Migration Best Practices

```csharp
// Custom migration with data seeding
public partial class SeedProducts : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // Create table
        migrationBuilder.CreateTable(
            name: "products",
            columns: table => new
            {
                product_id = table.Column<int>(nullable: false)
                    .Annotation("Npgsql:ValueGenerationStrategy", 
                        NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                product_name = table.Column<string>(maxLength: 100, nullable: false),
                unit_price = table.Column<decimal>(type: "decimal(10,2)", nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("pk_products", x => x.product_id);
            });

        // Create index
        migrationBuilder.CreateIndex(
            name: "ix_products_name",
            table: "products",
            column: "product_name");

        // Seed data
        migrationBuilder.InsertData(
            table: "products",
            columns: new[] { "product_name", "unit_price" },
            values: new object[,]
            {
                { "Widget", 19.99m },
                { "Gadget", 29.99m }
            });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "products");
    }
}
```

### Data Seeding in OnModelCreating

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    // Seed data
    modelBuilder.Entity<Category>().HasData(
        new Category { CategoryId = 1, CategoryName = "Electronics" },
        new Category { CategoryId = 2, CategoryName = "Clothing" },
        new Category { CategoryId = 3, CategoryName = "Books" }
    );

    // Seed with relationships
    modelBuilder.Entity<Product>().HasData(
        new Product 
        { 
            ProductId = 1, 
            ProductName = "Laptop", 
            CategoryId = 1,
            UnitPrice = 999.99m
        },
        new Product 
        { 
            ProductId = 2, 
            ProductName = "T-Shirt", 
            CategoryId = 2,
            UnitPrice = 19.99m
        }
    );
}
```

## Transactions

### Automatic Transactions

```csharp
// SaveChanges automatically wraps all changes in a transaction
public async Task UpdateCustomerAndOrders(int customerId)
{
    var customer = await context.Customers.FindAsync(customerId);
    customer.LastModified = DateTime.UtcNow;

    var orders = await context.Orders
        .Where(o => o.CustomerId == customerId)
        .ToListAsync();

    foreach (var order in orders)
    {
        order.Status = "Processed";
    }

    await context.SaveChangesAsync();  // All-or-nothing transaction
}
```

### Manual Transactions

```csharp
// Explicit transaction control
using var transaction = await context.Database.BeginTransactionAsync();

try
{
    // Multiple SaveChanges in one transaction
    var customer = new Customer { Name = "John Doe" };
    context.Customers.Add(customer);
    await context.SaveChangesAsync();

    var order = new Order 
    { 
        CustomerId = customer.CustomerId, 
        OrderDate = DateTime.UtcNow 
    };
    context.Orders.Add(order);
    await context.SaveChangesAsync();

    await transaction.CommitAsync();
}
catch (Exception)
{
    await transaction.RollbackAsync();
    throw;
}
```

### Transaction Isolation Levels

```csharp
// Set transaction isolation level
using var transaction = await context.Database.BeginTransactionAsync(
    IsolationLevel.ReadCommitted
);

try
{
    // Your operations here
    await context.SaveChangesAsync();
    await transaction.CommitAsync();
}
catch
{
    await transaction.RollbackAsync();
    throw;
}
```

## Performance Tips

### Bulk Operations

```csharp
// Bad: Individual inserts
foreach (var product in products)
{
    context.Products.Add(product);
    await context.SaveChangesAsync();  // Don't do this in loop!
}

// Good: Batch insert
context.Products.AddRange(products);
await context.SaveChangesAsync();

// Best: Use bulk extension (EFCore.BulkExtensions)
await context.BulkInsertAsync(products);
await context.BulkUpdateAsync(products);
await context.BulkDeleteAsync(products);
```

### Raw SQL Queries

```csharp
// Execute raw SQL query
var customers = await context.Customers
    .FromSqlRaw("SELECT * FROM customers WHERE country = {0}", "USA")
    .ToListAsync();

// Combine with LINQ
var filteredCustomers = await context.Customers
    .FromSqlRaw("SELECT * FROM customers WHERE country = 'USA'")
    .Where(c => c.IsActive)
    .OrderBy(c => c.Name)
    .ToListAsync();

// Execute non-query command
var rowsAffected = await context.Database
    .ExecuteSqlRawAsync(
        "UPDATE products SET unit_price = unit_price * 1.1 WHERE category_id = {0}",
        categoryId
    );
```

### Stored Procedures

```csharp
// Call stored procedure
var customers = await context.Customers
    .FromSqlRaw("EXEC GetCustomersByCountry @Country = {0}", "USA")
    .ToListAsync();

// Call stored procedure with output parameter
var countryParam = new SqlParameter("@Country", "USA");
var countParam = new SqlParameter
{
    ParameterName = "@Count",
    SqlDbType = SqlDbType.Int,
    Direction = ParameterDirection.Output
};

await context.Database.ExecuteSqlRawAsync(
    "EXEC GetCustomerCountByCountry @Country, @Count OUTPUT",
    countryParam,
    countParam
);

var count = (int)countParam.Value;
```

### Connection Resiliency

```csharp
// Configure retry policy
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseNpgsql(
        connectionString,
        npgsqlOptions =>
        {
            npgsqlOptions.EnableRetryOnFailure(
                maxRetryCount: 5,
                maxRetryDelay: TimeSpan.FromSeconds(30),
                errorCodesToAdd: null
            );
        }
    )
);

// Manual retry execution
var strategy = context.Database.CreateExecutionStrategy();

await strategy.ExecuteAsync(async () =>
{
    using var transaction = await context.Database.BeginTransactionAsync();
    
    // Your operations
    await context.SaveChangesAsync();
    
    await transaction.CommitAsync();
});
```

## Common Pitfalls

### 1. Modifying Collection During Iteration

```csharp
// Bad: Modifying collection while iterating
foreach (var order in customer.Orders)
{
    if (order.Status == "Cancelled")
    {
        customer.Orders.Remove(order);  // Exception!
    }
}

// Good: Use ToList() to create snapshot
foreach (var order in customer.Orders.ToList())
{
    if (order.Status == "Cancelled")
    {
        customer.Orders.Remove(order);
    }
}

// Better: Use RemoveAll (if available)
customer.Orders.RemoveAll(o => o.Status == "Cancelled");
```

### 2. Not Disposing DbContext

```csharp
// Bad: DbContext not disposed
public List<Customer> GetCustomers()
{
    var context = new ApplicationDbContext();
    return context.Customers.ToList();  // Memory leak!
}

// Good: Use using statement
public List<Customer> GetCustomers()
{
    using var context = new ApplicationDbContext();
    return context.Customers.ToList();
}

// Best: Use dependency injection
public class CustomerService
{
    private readonly ApplicationDbContext _context;

    public CustomerService(ApplicationDbContext context)
    {
        _context = context;  // Managed by DI container
    }
}
```

### 3. Client-Side Evaluation

```csharp
// Bad: Calls C# method in query (client-side evaluation)
var customers = await context.Customers
    .Where(c => IsValidEmail(c.Email))  // Executes in C#, not SQL!
    .ToListAsync();

// Good: Use database functions
var customers = await context.Customers
    .Where(c => EF.Functions.Like(c.Email, "%@%.%"))
    .ToListAsync();
```

### 4. Loading Too Much Data

```csharp
// Bad: Loading everything into memory
var allCustomers = await context.Customers.ToListAsync();
var activeCustomers = allCustomers.Where(c => c.IsActive);  // Filtered in memory!

// Good: Filter in database
var activeCustomers = await context.Customers
    .Where(c => c.IsActive)
    .ToListAsync();
```

### 5. Ignoring Async/Await

```csharp
// Bad: Blocking async call
var customers = context.Customers.ToListAsync().Result;  // Deadlock risk!

// Good: Await properly
var customers = await context.Customers.ToListAsync();
```

## Performance Monitoring

### Enable Logging

```csharp
// Log all SQL queries
builder.Services.AddDbContext<ApplicationDbContext>(options =>
{
    options.UseNpgsql(connectionString)
        .LogTo(
            Console.WriteLine,
            new[] { DbLoggerCategory.Database.Command.Name },
            LogLevel.Information
        )
        .EnableSensitiveDataLogging();  // Shows parameter values
});
```

### Query Statistics

```csharp
// Track query execution time
var stopwatch = Stopwatch.StartNew();

var customers = await context.Customers
    .Include(c => c.Orders)
    .ToListAsync();

stopwatch.Stop();
logger.LogInformation(
    "Query executed in {ElapsedMs}ms, returned {Count} customers",
    stopwatch.ElapsedMilliseconds,
    customers.Count
);
```

## Best Practices Summary

Configuration:
- [ ] Use dependency injection for DbContext
- [ ] Enable connection resiliency
- [ ] Configure appropriate timeouts
- [ ] Use connection pooling

Queries:
- [ ] Use AsNoTracking for read-only queries
- [ ] Project to DTOs instead of loading full entities
- [ ] Avoid N+1 queries with Include
- [ ] Use compiled queries for frequently executed queries

Performance:
- [ ] Use bulk operations for large datasets
- [ ] Implement paging for large result sets
- [ ] Use split queries for multiple collections
- [ ] Monitor and log slow queries

Maintenance:
- [ ] Keep migrations organized and named clearly
- [ ] Test migrations in development before production
- [ ] Use transactions for related operations
- [ ] Regular database maintenance and indexing

Security:
- [ ] Use parameterized queries (EF does this automatically)
- [ ] Validate input data
- [ ] Implement proper authorization
- [ ] Encrypt sensitive data
