# Common Errors and Solutions

## Table of Contents
1. [SQL Errors](#sql-errors)
2. [C# Runtime Errors](#c-runtime-errors)
3. [Async/Await Errors](#asyncawait-errors)
4. [Entity Framework Errors](#entity-framework-errors)
5. [Web API Errors](#web-api-errors)
6. [Performance Issues](#performance-issues)
7. [Security Vulnerabilities](#security-vulnerabilities)

## SQL Errors

### Syntax Errors

#### Missing Semicolon
```sql
-- Error: Missing semicolon
SELECT * FROM products
SELECT * FROM customers

-- Solution: Add semicolon to separate statements
SELECT * FROM products;
SELECT * FROM customers;
```

#### Unmatched Quotes
```sql
-- Error: Unmatched quotes
SELECT * FROM customers WHERE name = "John';

-- Solution: Use consistent quote types (single quotes for strings)
SELECT * FROM customers WHERE name = 'John';
```

#### Reserved Keywords
```sql
-- Error: Using reserved keyword without quotes
SELECT order FROM orders;

-- Solution: Quote column names that are keywords
SELECT "order" FROM orders;

-- Better: Avoid using reserved keywords as column names
SELECT order_number FROM orders;
```

### Join Errors

#### Missing JOIN Condition
```sql
-- Error: Cartesian product (all combinations)
SELECT * FROM customers, orders;

-- Solution: Always specify JOIN condition
SELECT * FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;
```

#### Ambiguous Column Names
```sql
-- Error: Column exists in both tables
SELECT customer_id, order_date
FROM customers
INNER JOIN orders ON customers.customer_id = orders.customer_id;

-- Solution: Use table aliases
SELECT c.customer_id, o.order_date
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;
```

### Data Type Errors

#### Type Mismatch in Comparisons
```sql
-- Error: Comparing string to integer
SELECT * FROM orders WHERE order_id = '123';

-- Solution: Use correct data type
SELECT * FROM orders WHERE order_id = 123;

-- Or cast explicitly
SELECT * FROM orders WHERE order_id = CAST('123' AS INTEGER);
```

#### NULL Comparison Errors
```sql
-- Error: NULL comparisons don't work with = or !=
SELECT * FROM customers WHERE email = NULL;

-- Solution: Use IS NULL or IS NOT NULL
SELECT * FROM customers WHERE email IS NULL;
SELECT * FROM customers WHERE email IS NOT NULL;
```

### Aggregation Errors

#### SELECT Without GROUP BY
```sql
-- Error: Mixing aggregated and non-aggregated columns
SELECT customer_id, COUNT(*)
FROM orders;

-- Solution: Include non-aggregated columns in GROUP BY
SELECT customer_id, COUNT(*)
FROM orders
GROUP BY customer_id;
```

#### Using WHERE Instead of HAVING
```sql
-- Error: Can't use aggregate functions in WHERE
SELECT customer_id, COUNT(*) as order_count
FROM orders
WHERE COUNT(*) > 5
GROUP BY customer_id;

-- Solution: Use HAVING for aggregate conditions
SELECT customer_id, COUNT(*) as order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 5;
```

### Performance Issues

#### Missing Indexes
```sql
-- Problem: Slow query due to missing index
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;
-- Shows: Seq Scan on orders (slow!)

-- Solution: Create index on frequently queried columns
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

#### N+1 Query Problem
```sql
-- Problem: One query per row
-- Query 1: Get all customers
SELECT * FROM customers;

-- Query 2-N: Get orders for each customer (in application loop)
SELECT * FROM orders WHERE customer_id = 1;
SELECT * FROM orders WHERE customer_id = 2;
-- ... repeated for each customer

-- Solution: Use JOIN to get all data in one query
SELECT 
    c.customer_id,
    c.company_name,
    COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name;
```

#### Inefficient LIKE Queries
```sql
-- Problem: Leading wildcard prevents index usage
SELECT * FROM customers WHERE company_name LIKE '%construction%';

-- Solution: Use full-text search for complex text searches
SELECT * FROM customers 
WHERE to_tsvector('english', company_name) @@ to_tsquery('construction');

-- Or if trailing match is sufficient, use trailing wildcard only
SELECT * FROM customers WHERE company_name LIKE 'construction%';
```

## C# Runtime Errors

### NullReferenceException

```csharp
// Problem: Accessing member on null object
string name = user.Name;  // NullReferenceException if user is null

// Solution 1: Null check
if (user != null)
{
    string name = user.Name;
}

// Solution 2: Null-conditional operator (C# 6+)
string name = user?.Name;

// Solution 3: Null-coalescing operator
string name = user?.Name ?? "Unknown";

// Solution 4: Nullable reference types (C# 8+)
public class UserService
{
    // Enable nullable reference types in .csproj
    // <Nullable>enable</Nullable>
    
    public string GetUserName(User? user)  // ? indicates nullable
    {
        return user?.Name ?? "Unknown";  // Compiler warns if not checked
    }
}
```

### IndexOutOfRangeException

```csharp
// Problem: Accessing invalid array index
var items = new[] { 1, 2, 3 };
var item = items[5];  // IndexOutOfRangeException

// Solution 1: Check bounds
if (index >= 0 && index < items.Length)
{
    var item = items[index];
}

// Solution 2: Use ElementAtOrDefault (LINQ)
var item = items.ElementAtOrDefault(5);  // Returns 0 (default) instead of exception

// Solution 3: Try-catch (last resort)
try
{
    var item = items[index];
}
catch (IndexOutOfRangeException)
{
    // Handle error
}
```

### InvalidOperationException

```csharp
// Problem: Collection modified during iteration
var list = new List<int> { 1, 2, 3, 4, 5 };
foreach (var item in list)
{
    if (item % 2 == 0)
        list.Remove(item);  // InvalidOperationException!
}

// Solution 1: Iterate backwards with for loop
for (int i = list.Count - 1; i >= 0; i--)
{
    if (list[i] % 2 == 0)
        list.RemoveAt(i);
}

// Solution 2: Use ToList() to create snapshot
foreach (var item in list.ToList())
{
    if (item % 2 == 0)
        list.Remove(item);
}

// Solution 3: Use RemoveAll (best for this scenario)
list.RemoveAll(item => item % 2 == 0);

// Solution 4: Create new list
var newList = list.Where(item => item % 2 != 0).ToList();
```

### KeyNotFoundException

```csharp
// Problem: Accessing non-existent dictionary key
var dict = new Dictionary<string, int> { { "apple", 5 } };
var value = dict["banana"];  // KeyNotFoundException

// Solution 1: Check if key exists
if (dict.ContainsKey("banana"))
{
    var value = dict["banana"];
}

// Solution 2: Use TryGetValue (preferred)
if (dict.TryGetValue("banana", out var value))
{
    // Use value
    Console.WriteLine(value);
}
else
{
    // Handle missing key
    Console.WriteLine("Key not found");
}

// Solution 3: Use GetValueOrDefault (C# 9+)
var value = dict.GetValueOrDefault("banana", 0);  // Returns 0 if not found
```

### ObjectDisposedException

```csharp
// Problem: Using disposed object
var stream = new FileStream("file.txt", FileMode.Open);
stream.Dispose();
stream.Read(buffer, 0, buffer.Length);  // ObjectDisposedException

// Solution 1: Don't use after disposing
using (var stream = new FileStream("file.txt", FileMode.Open))
{
    stream.Read(buffer, 0, buffer.Length);
}  // Auto-disposed here, don't use after

// Solution 2: Using declaration (C# 8+)
using var stream = new FileStream("file.txt", FileMode.Open);
stream.Read(buffer, 0, buffer.Length);
// Auto-disposed at end of scope

// Solution 3: Check if disposed (if applicable)
if (!stream.CanRead)
{
    // Stream is disposed or not readable
    throw new InvalidOperationException("Stream is not readable");
}
```

## Async/Await Errors

### Deadlock on .Result or .Wait()

```csharp
// Problem: Blocking on async code causes deadlock
public void ProcessData()
{
    var result = GetDataAsync().Result;  // DEADLOCK in UI/ASP.NET contexts
}

public async Task<string> GetDataAsync()
{
    await Task.Delay(1000);
    return "data";
}

// Solution 1: Make method async all the way
public async Task ProcessDataAsync()
{
    var result = await GetDataAsync();
}

// Solution 2: Use ConfigureAwait(false) in library code
public async Task<string> GetDataAsync()
{
    await Task.Delay(1000).ConfigureAwait(false);
    return "data";
}

// Solution 3: Run synchronously if needed (not recommended)
public void ProcessData()
{
    var result = Task.Run(() => GetDataAsync()).Result;
}
```

### Async Void Anti-Pattern

```csharp
// Problem: async void swallows exceptions and can't be awaited
public async void ProcessDataAsync()  // DON'T DO THIS
{
    await Task.Delay(1000);
    throw new Exception("Error!");  // Exception is lost!
}

// Solution: Use async Task
public async Task ProcessDataAsync()
{
    await Task.Delay(1000);
    throw new Exception("Error!");  // Exception can be caught
}

// Exception: Event handlers must be async void
private async void Button_Click(object sender, EventArgs e)
{
    try
    {
        await ProcessDataAsync();
    }
    catch (Exception ex)
    {
        // Handle exception
        MessageBox.Show(ex.Message);
    }
}
```

### Not Awaiting Tasks

```csharp
// Problem: Task not awaited - fire and forget
public async Task ProcessOrdersAsync()
{
    SendNotificationAsync();  // Not awaited! Continues without waiting
    await SaveToDatabase();
}

// Solution 1: Await the task
public async Task ProcessOrdersAsync()
{
    await SendNotificationAsync();
    await SaveToDatabase();
}

// Solution 2: Run in parallel if independent
public async Task ProcessOrdersAsync()
{
    var notificationTask = SendNotificationAsync();
    var saveTask = SaveToDatabase();
    await Task.WhenAll(notificationTask, saveTask);
}

// Solution 3: Intentional fire-and-forget with error handling
public async Task ProcessOrdersAsync()
{
    _ = Task.Run(async () =>
    {
        try
        {
            await SendNotificationAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Notification failed");
        }
    });
    
    await SaveToDatabase();
}
```

### TaskCanceledException Not Handled

```csharp
// Problem: Not handling cancellation
public async Task<Data> FetchDataAsync(CancellationToken cancellationToken)
{
    return await _httpClient.GetFromJsonAsync<Data>(url, cancellationToken);
    // TaskCanceledException if cancelled
}

// Solution: Handle cancellation appropriately
public async Task<Data> FetchDataAsync(CancellationToken cancellationToken)
{
    try
    {
        return await _httpClient.GetFromJsonAsync<Data>(url, cancellationToken);
    }
    catch (TaskCanceledException)
    {
        _logger.LogInformation("Request was cancelled");
        return null;  // Or throw, depending on requirements
    }
    catch (OperationCanceledException)
    {
        _logger.LogInformation("Operation was cancelled");
        return null;
    }
}
```

## Entity Framework Errors

### DbUpdateConcurrencyException

```csharp
// Problem: Optimistic concurrency conflict
var product = await context.Products.FindAsync(1);
product.Price = 99.99m;
await context.SaveChangesAsync();  // Another user updated it first!

// Solution 1: Retry with fresh data
try
{
    await context.SaveChangesAsync();
}
catch (DbUpdateConcurrencyException ex)
{
    var entry = ex.Entries.Single();
    var databaseValues = await entry.GetDatabaseValuesAsync();
    
    if (databaseValues == null)
    {
        // Entity was deleted
        throw new Exception("Entity was deleted by another user");
    }
    
    // Refresh and retry
    entry.OriginalValues.SetValues(databaseValues);
    await context.SaveChangesAsync();
}

// Solution 2: Use row version for concurrency control
public class Product
{
    public int ProductId { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
    
    [Timestamp]
    public byte[] RowVersion { get; set; }  // Concurrency token
}
```

### Tracking Errors

```csharp
// Problem: Entity already tracked with different instance
var product1 = await context.Products.FindAsync(1);
var product2 = new Product { ProductId = 1, Name = "Updated" };
context.Products.Update(product2);  // Error: Instance already tracked!

// Solution 1: Use the tracked instance
var product = await context.Products.FindAsync(1);
product.Name = "Updated";
await context.SaveChangesAsync();

// Solution 2: Detach existing instance
var product1 = await context.Products.FindAsync(1);
context.Entry(product1).State = EntityState.Detached;
var product2 = new Product { ProductId = 1, Name = "Updated" };
context.Products.Update(product2);

// Solution 3: Use AsNoTracking for read operations
var product = await context.Products.AsNoTracking().FindAsync(1);
```

### N+1 Query Problem

```csharp
// Problem: Lazy loading causes multiple queries
var customers = await context.Customers.ToListAsync();
foreach (var customer in customers)
{
    // Each iteration triggers a new query!
    var orderCount = customer.Orders.Count();
}

// Solution 1: Eager loading with Include
var customers = await context.Customers
    .Include(c => c.Orders)
    .ToListAsync();

// Solution 2: Projection (best for counts/aggregates)
var customerSummaries = await context.Customers
    .Select(c => new
    {
        c.CustomerId,
        c.Name,
        OrderCount = c.Orders.Count()
    })
    .ToListAsync();
```

## Web API Errors

### Model Binding Failures

```csharp
// Problem: Request data doesn't match model
[HttpPost]
public IActionResult Create([FromBody] Product product)
{
    // product is null if JSON doesn't match
    if (product == null)
        return BadRequest();
    
    // ModelState.IsValid is false if validation fails
}

// Solution: Check ModelState
[HttpPost]
public IActionResult Create([FromBody] Product product)
{
    if (product == null)
        return BadRequest("Product data is required");
    
    if (!ModelState.IsValid)
    {
        return BadRequest(ModelState);
    }
    
    // Process valid product
    return Ok();
}
```

### CORS Errors

```csharp
// Problem: Cross-origin requests blocked
// Error: "No 'Access-Control-Allow-Origin' header is present"

// Solution: Configure CORS in Program.cs
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowSpecificOrigin",
        builder =>
        {
            builder.WithOrigins("https://example.com")
                   .AllowAnyMethod()
                   .AllowAnyHeader();
        });
});

var app = builder.Build();
app.UseCors("AllowSpecificOrigin");
```

### Unhandled Exceptions

```csharp
// Problem: Exceptions return 500 with stack trace in production

// Solution: Global exception handler
app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        context.Response.StatusCode = 500;
        context.Response.ContentType = "application/json";
        
        var error = context.Features.Get<IExceptionHandlerFeature>();
        if (error != null)
        {
            var logger = context.RequestServices.GetRequiredService<ILogger<Program>>();
            logger.LogError(error.Error, "Unhandled exception");
            
            await context.Response.WriteAsJsonAsync(new
            {
                error = "An error occurred processing your request",
                // Don't expose stack trace in production
            });
        }
    });
});
```

## Performance Issues

### Memory Leaks

```csharp
// Problem: Event handlers not unsubscribed
public class EventPublisher
{
    public event EventHandler DataReceived;
    
    public void RaiseEvent()
    {
        DataReceived?.Invoke(this, EventArgs.Empty);
    }
}

public class EventSubscriber
{
    public EventSubscriber(EventPublisher publisher)
    {
        publisher.DataReceived += OnDataReceived;  // Memory leak!
    }
    
    private void OnDataReceived(object sender, EventArgs e) { }
}

// Solution: Unsubscribe when done
public class EventSubscriber : IDisposable
{
    private readonly EventPublisher _publisher;
    
    public EventSubscriber(EventPublisher publisher)
    {
        _publisher = publisher;
        _publisher.DataReceived += OnDataReceived;
    }
    
    private void OnDataReceived(object sender, EventArgs e) { }
    
    public void Dispose()
    {
        _publisher.DataReceived -= OnDataReceived;  // Unsubscribe!
    }
}
```

### String Concatenation in Loops

```csharp
// Problem: String concatenation in loop (creates many objects)
string result = "";
for (int i = 0; i < 10000; i++)
{
    result += i.ToString() + ",";  // Very slow!
}

// Solution: Use StringBuilder
var sb = new StringBuilder();
for (int i = 0; i < 10000; i++)
{
    sb.Append(i).Append(",");
}
var result = sb.ToString();

// Or use string.Join for collections
var result = string.Join(",", Enumerable.Range(0, 10000));
```

### Synchronous I/O in Async Context

```csharp
// Problem: Blocking I/O in async method
public async Task<string> ReadFileAsync(string path)
{
    using var reader = new StreamReader(path);
    return reader.ReadToEnd();  // Synchronous! Blocks thread!
}

// Solution: Use async I/O
public async Task<string> ReadFileAsync(string path)
{
    using var reader = new StreamReader(path);
    return await reader.ReadToEndAsync();
}
```

## Security Vulnerabilities

### SQL Injection

```csharp
// Problem: String concatenation in SQL
var query = $"SELECT * FROM users WHERE username = '{username}'";
// Attacker inputs: ' OR '1'='1

// Solution: Use parameterized queries
var query = "SELECT * FROM users WHERE username = @username";
using var cmd = new SqlCommand(query, connection);
cmd.Parameters.AddWithValue("@username", username);

// Or use Entity Framework (automatically parameterized)
var user = await context.Users
    .FirstOrDefaultAsync(u => u.Username == username);
```

### Cross-Site Scripting (XSS)

```csharp
// Problem: Unescaped user input in HTML
public IActionResult Display(string message)
{
    ViewBag.Message = message;  // Dangerous if rendered as HTML
    return View();
}

// Solution: Use proper encoding
@Html.Encode(ViewBag.Message)  // In Razor view

// Or use @Html.Raw() only for trusted content
```

### Insecure Deserialization

```csharp
// Problem: Deserializing untrusted data
var obj = JsonConvert.DeserializeObject<object>(untrustedJson);  // Dangerous

// Solution: Deserialize to specific types only
var product = JsonConvert.DeserializeObject<Product>(json);

// Validate after deserialization
if (product == null || string.IsNullOrEmpty(product.Name))
{
    throw new ArgumentException("Invalid product data");
}
```

## Best Practices Summary

Prevention:
- [ ] Enable nullable reference types (C# 8+)
- [ ] Use static code analysis tools
- [ ] Write unit tests
- [ ] Enable all compiler warnings
- [ ] Use code reviews

Error Handling:
- [ ] Catch specific exceptions, not generic Exception
- [ ] Log errors with context
- [ ] Don't swallow exceptions
- [ ] Use proper async error handling
- [ ] Return appropriate error responses in APIs

Performance:
- [ ] Profile before optimizing
- [ ] Use async for I/O operations
- [ ] Avoid premature optimization
- [ ] Monitor production performance
- [ ] Use connection pooling

Security:
- [ ] Never trust user input
- [ ] Use parameterized queries
- [ ] Validate and sanitize input
- [ ] Implement proper authentication/authorization
- [ ] Keep dependencies updated
