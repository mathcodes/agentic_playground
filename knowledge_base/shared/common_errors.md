# Common Errors and Solutions

## SQL Errors

### Syntax Errors
- **Missing semicolon**: Always end SQL statements with `;`
- **Unmatched quotes**: Use single quotes for strings in SQL
- **Reserved keywords**: Use quotes for column names that are keywords

### Performance Issues
- **N+1 queries**: Use JOIN instead of multiple queries
- **Missing indexes**: Add indexes on frequently queried columns
- **SELECT ***: Only select columns you need

## C# Errors

### NullReferenceException
```csharp
// Problem
string name = user.Name; // user might be null

// Solution 1: Null check
if (user != null)
{
    string name = user.Name;
}

// Solution 2: Null-conditional operator
string name = user?.Name;

// Solution 3: Null-coalescing
string name = user?.Name ?? "Unknown";
```

### Task.Result Deadlock
```csharp
// Problem
var result = GetDataAsync().Result; // Can deadlock

// Solution
var result = await GetDataAsync();
```

### Collection Modified Exception
```csharp
// Problem
foreach (var item in list)
{
    list.Remove(item); // Can't modify during iteration
}

// Solution
for (int i = list.Count - 1; i >= 0; i--)
{
    list.RemoveAt(i);
}
```

## General Best Practices

- Always validate user input
- Use parameterized queries to prevent SQL injection
- Handle exceptions appropriately
- Log errors for debugging
- Write unit tests for critical code
