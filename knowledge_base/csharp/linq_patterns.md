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
