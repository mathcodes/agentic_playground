# LINQ Query Patterns

## Common LINQ Operations

### Filtering with Where
```csharp
// Filter items based on a condition
var adults = users.Where(u => u.Age >= 18).ToList();

// Multiple conditions
var activeAdults = users
    .Where(u => u.Age >= 18 && u.IsActive)
    .ToList();
```

### Selecting/Projecting with Select
```csharp
// Select specific properties
var names = users.Select(u => u.Name).ToList();

// Project to anonymous type
var userSummary = users.Select(u => new 
{
    u.Name,
    u.Email,
    IsAdult = u.Age >= 18
}).ToList();

// Project to DTO
var dtos = users.Select(u => new UserDto
{
    Name = u.Name,
    Email = u.Email
}).ToList();
```

### Ordering with OrderBy/OrderByDescending
```csharp
// Simple ordering
var sorted = users.OrderBy(u => u.Name).ToList();

// Descending order
var sortedDesc = users.OrderByDescending(u => u.Age).ToList();

// Multiple sort criteria
var multiSort = users
    .OrderBy(u => u.LastName)
    .ThenBy(u => u.FirstName)
    .ToList();
```

### Grouping with GroupBy
```csharp
// Group by single property
var byAge = users.GroupBy(u => u.Age);

// Group and aggregate
var ageCounts = users
    .GroupBy(u => u.Age)
    .Select(g => new 
    {
        Age = g.Key,
        Count = g.Count()
    })
    .ToList();
```

### Joining Collections
```csharp
// Inner join
var ordersWithCustomers = orders
    .Join(
        customers,
        o => o.CustomerId,
        c => c.Id,
        (o, c) => new { Order = o, Customer = c }
    )
    .ToList();

// Left join (GroupJoin)
var customersWithOrders = customers
    .GroupJoin(
        orders,
        c => c.Id,
        o => o.CustomerId,
        (c, orderGroup) => new 
        {
            Customer = c,
            Orders = orderGroup.ToList()
        }
    )
    .ToList();
```

## Advanced Patterns

### Any/All
```csharp
// Check if any match
bool hasAdults = users.Any(u => u.Age >= 18);

// Check if all match
bool allActive = users.All(u => u.IsActive);
```

### First/FirstOrDefault
```csharp
// Get first or throw exception
var first = users.First(u => u.Name == "John");

// Get first or null
var firstOrNull = users.FirstOrDefault(u => u.Name == "John");
```

### Aggregations
```csharp
// Count
int count = users.Count();
int adultCount = users.Count(u => u.Age >= 18);

// Sum
decimal total = orders.Sum(o => o.Total);

// Average
double avgAge = users.Average(u => u.Age);

// Min/Max
int minAge = users.Min(u => u.Age);
int maxAge = users.Max(u => u.Age);
```

## Query Syntax vs Method Syntax

### Query Syntax
```csharp
var adults = from u in users
             where u.Age >= 18
             orderby u.Name
             select u;
```

### Method Syntax (Preferred)
```csharp
var adults = users
    .Where(u => u.Age >= 18)
    .OrderBy(u => u.Name)
    .ToList();
```

## IEnumerable vs IQueryable

### IEnumerable (In-Memory)
```csharp
// Executes immediately in memory
IEnumerable<User> users = GetUsers();
var filtered = users.Where(u => u.Age > 18); // LINQ to Objects
```

### IQueryable (Database Query)
```csharp
// Builds expression tree, executes on database
IQueryable<User> users = dbContext.Users;
var filtered = users.Where(u => u.Age > 18); // LINQ to Entities
```

## Performance Tips

1. **Use ToList() carefully** - It executes the query immediately
2. **Defer execution** - Queries execute when enumerated
3. **Use AsNoTracking()** for read-only queries in EF
4. **Avoid N+1 queries** - Use Include() for related data

## Advanced LINQ Patterns

### Set Operations

```csharp
var list1 = new[] { 1, 2, 3, 4, 5 };
var list2 = new[] { 4, 5, 6, 7, 8 };

// Union (distinct elements from both)
var union = list1.Union(list2);  // 1,2,3,4,5,6,7,8

// Intersect (common elements)
var intersection = list1.Intersect(list2);  // 4,5

// Except (elements in first but not second)
var difference = list1.Except(list2);  // 1,2,3

// Concat (all elements, including duplicates)
var concatenated = list1.Concat(list2);  // 1,2,3,4,5,4,5,6,7,8
```

### Partitioning

```csharp
var numbers = Enumerable.Range(1, 100);

// Take first N elements
var firstTen = numbers.Take(10);

// Skip first N elements
var afterTen = numbers.Skip(10);

// Take while condition is true
var lessThanFifty = numbers.TakeWhile(n => n < 50);

// Skip while condition is true
var fiftyAndAbove = numbers.SkipWhile(n => n < 50);

// Pagination pattern
int pageSize = 20;
int pageNumber = 2;
var page = numbers
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize);
```

### Complex Aggregations

```csharp
var numbers = new[] { 1, 2, 3, 4, 5 };

// Aggregate with seed and accumulator
var sum = numbers.Aggregate(0, (acc, n) => acc + n);  // 15

// Aggregate with complex logic
var product = numbers.Aggregate(1, (acc, n) => acc * n);  // 120

// Aggregate with result selector
var stats = numbers.Aggregate(
    new { Sum = 0, Count = 0 },
    (acc, n) => new { Sum = acc.Sum + n, Count = acc.Count + 1 },
    result => new { result.Sum, result.Count, Average = (double)result.Sum / result.Count }
);

// Multiple aggregations in one pass
var summary = orders
    .GroupBy(o => 1)
    .Select(g => new
    {
        TotalOrders = g.Count(),
        TotalRevenue = g.Sum(o => o.Total),
        AverageOrderValue = g.Average(o => o.Total),
        MaxOrderValue = g.Max(o => o.Total),
        MinOrderValue = g.Min(o => o.Total)
    })
    .FirstOrDefault();
```

### Lookup Pattern

```csharp
// Create a lookup (like dictionary but allows multiple values per key)
var ordersByCustomer = orders.ToLookup(o => o.CustomerId);

// Access orders for specific customer
var customer123Orders = ordersByCustomer[123];

// Check if customer has orders
bool hasOrders = ordersByCustomer.Contains(123);

// Iterate through all groups
foreach (var customerGroup in ordersByCustomer)
{
    Console.WriteLine($"Customer {customerGroup.Key} has {customerGroup.Count()} orders");
}
```

### Zip Pattern

```csharp
// Combine two sequences element-by-element
var names = new[] { "Alice", "Bob", "Charlie" };
var scores = new[] { 95, 87, 92 };

var results = names.Zip(scores, (name, score) => new { Name = name, Score = score });
// Results: { Alice, 95 }, { Bob, 87 }, { Charlie, 92 }

// Zip with index
var indexed = names.Select((name, index) => new { Index = index, Name = name });
```

### SelectMany (Flattening)

```csharp
// Flatten nested collections
var departments = new[]
{
    new { Name = "IT", Employees = new[] { "Alice", "Bob" } },
    new { Name = "HR", Employees = new[] { "Charlie", "David" } }
};

// Get all employees from all departments
var allEmployees = departments.SelectMany(d => d.Employees);
// Result: Alice, Bob, Charlie, David

// SelectMany with result selector
var employeeWithDept = departments.SelectMany(
    d => d.Employees,
    (dept, employee) => new { Department = dept.Name, Employee = employee }
);
```

### Complex Filtering

```csharp
// OfType - filter by type
var mixed = new object[] { 1, "two", 3, "four", 5 };
var numbers = mixed.OfType<int>();  // 1, 3, 5
var strings = mixed.OfType<string>();  // "two", "four"

// Multiple conditions with logical operators
var filtered = products
    .Where(p => 
        (p.CategoryId == 1 || p.CategoryId == 2) &&
        p.UnitPrice > 10 &&
        p.UnitPrice < 100 &&
        p.UnitsInStock > 0
    );

// Distinct with custom comparer
public class ProductComparer : IEqualityComparer<Product>
{
    public bool Equals(Product x, Product y) => x.CategoryId == y.CategoryId;
    public int GetHashCode(Product obj) => obj.CategoryId.GetHashCode();
}

var uniqueCategories = products.Distinct(new ProductComparer());
```

### GroupJoin Pattern

```csharp
// Left join in LINQ
var customersWithOrders = customers.GroupJoin(
    orders,
    customer => customer.CustomerId,
    order => order.CustomerId,
    (customer, orderGroup) => new
    {
        Customer = customer,
        Orders = orderGroup.ToList(),
        OrderCount = orderGroup.Count(),
        TotalSpent = orderGroup.Sum(o => o.Total)
    }
);

// Customers with no orders
var customersWithoutOrders = customers
    .GroupJoin(
        orders,
        c => c.CustomerId,
        o => o.CustomerId,
        (c, orderGroup) => new { Customer = c, HasOrders = orderGroup.Any() }
    )
    .Where(x => !x.HasOrders)
    .Select(x => x.Customer);
```

### DefaultIfEmpty Pattern

```csharp
// Handle empty sequences
var numbers = new int[] { };
var defaultValue = numbers.DefaultIfEmpty(0).First();  // Returns 0

// Left join with DefaultIfEmpty
var leftJoin = from c in customers
               join o in orders on c.CustomerId equals o.CustomerId into orderGroup
               from o in orderGroup.DefaultIfEmpty()
               select new
               {
                   Customer = c,
                   OrderId = o?.OrderId,
                   OrderTotal = o?.Total ?? 0
               };
```

### Quantifiers

```csharp
// Any - check if at least one element satisfies condition
bool hasExpensiveProducts = products.Any(p => p.UnitPrice > 1000);

// All - check if all elements satisfy condition
bool allInStock = products.All(p => p.UnitsInStock > 0);

// Contains - check if sequence contains specific element
bool hasProductId5 = products.Select(p => p.ProductId).Contains(5);

// SequenceEqual - check if two sequences are equal
bool areEqual = list1.SequenceEqual(list2);
```

### Performance Optimization Patterns

```csharp
// Materialize once if reusing
var activeCustomers = customers.Where(c => c.IsActive).ToList();
// Now activeCustomers can be enumerated multiple times without re-querying

// Deferred execution - query not executed yet
var query = customers.Where(c => c.Country == "USA");
// Query executes here when enumerated:
foreach (var customer in query) { }

// Immediate execution
var list = customers.Where(c => c.Country == "USA").ToList();  // Executes immediately
var count = customers.Count(c => c.Country == "USA");  // Executes immediately
var first = customers.First(c => c.Country == "USA");  // Executes immediately

// Avoid multiple enumerations
// Bad:
var filtered = customers.Where(c => c.IsActive);
var count = filtered.Count();  // Query 1
var items = filtered.ToList();  // Query 2

// Good:
var filtered = customers.Where(c => c.IsActive).ToList();
var count = filtered.Count;  // No query
var items = filtered;  // No query
```

### Custom LINQ Extensions

```csharp
// Create custom LINQ extension methods
public static class LinqExtensions
{
    // Distinct by property
    public static IEnumerable<T> DistinctBy<T, TKey>(
        this IEnumerable<T> source,
        Func<T, TKey> keySelector)
    {
        var seenKeys = new HashSet<TKey>();
        foreach (var element in source)
        {
            if (seenKeys.Add(keySelector(element)))
            {
                yield return element;
            }
        }
    }

    // Batch processing
    public static IEnumerable<IEnumerable<T>> Batch<T>(
        this IEnumerable<T> source,
        int batchSize)
    {
        var batch = new List<T>(batchSize);
        foreach (var item in source)
        {
            batch.Add(item);
            if (batch.Count == batchSize)
            {
                yield return batch;
                batch = new List<T>(batchSize);
            }
        }
        if (batch.Count > 0)
        {
            yield return batch;
        }
    }

    // ForEach (not standard LINQ but useful)
    public static void ForEach<T>(
        this IEnumerable<T> source,
        Action<T> action)
    {
        foreach (var item in source)
        {
            action(item);
        }
    }
}

// Usage
var uniqueProducts = products.DistinctBy(p => p.ProductName);
var batches = products.Batch(100);
customers.Where(c => c.IsActive).ForEach(c => SendEmail(c));
```

## LINQ Best Practices Summary

Performance:
- [ ] Use ToList() only when necessary
- [ ] Understand deferred vs immediate execution
- [ ] Avoid multiple enumerations of same query
- [ ] Use AsNoTracking() for read-only EF queries
- [ ] Filter early, project late

Readability:
- [ ] Prefer method syntax over query syntax
- [ ] Use meaningful variable names
- [ ] Break complex queries into smaller parts
- [ ] Consider custom extension methods for reusable logic

Common Patterns:
- [ ] Use Any() instead of Count() > 0
- [ ] Use FirstOrDefault() instead of Where().First()
- [ ] Use SingleOrDefault() when expecting one or zero results
- [ ] Leverage GroupBy for aggregations
- [ ] Use SelectMany to flatten nested collections
