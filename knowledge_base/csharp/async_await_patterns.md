# Async/Await Patterns in C#

## Basic Async/Await

### Async Method Declaration
```csharp
public async Task<string> GetDataAsync()
{
    await Task.Delay(1000);
    return "Data loaded";
}

// Void async (avoid except for event handlers)
public async void ButtonClick(object sender, EventArgs e)
{
    await ProcessAsync();
}
```

### Awaiting Tasks
```csharp
// Single await
var result = await GetDataAsync();

// Multiple sequential awaits
var user = await GetUserAsync(id);
var orders = await GetOrdersAsync(user.Id);

// Multiple parallel awaits
var userTask = GetUserAsync(id);
var ordersTask = GetOrdersAsync(id);
await Task.WhenAll(userTask, ordersTask);
```

## Common Patterns

### Task.WhenAll (Parallel Execution)
```csharp
public async Task<List<Result>> GetAllDataAsync()
{
    var tasks = new List<Task<Result>>
    {
        FetchDataFromApi1Async(),
        FetchDataFromApi2Async(),
        FetchDataFromApi3Async()
    };
    
    var results = await Task.WhenAll(tasks);
    return results.ToList();
}
```

### Task.WhenAny (First to Complete)
```csharp
public async Task<string> GetFirstResponseAsync()
{
    var task1 = FetchFromServer1Async();
    var task2 = FetchFromServer2Async();
    
    var completedTask = await Task.WhenAny(task1, task2);
    return await completedTask;
}
```

### ConfigureAwait(false)
```csharp
// In library code, use ConfigureAwait(false)
public async Task ProcessAsync()
{
    var data = await GetDataAsync().ConfigureAwait(false);
    // Don't need to return to original context
    await SaveDataAsync(data).ConfigureAwait(false);
}
```

## ASP.NET Core Patterns

### Controller Actions
```csharp
[HttpGet("{id}")]
public async Task<ActionResult<User>> GetUser(int id)
{
    var user = await _context.Users.FindAsync(id);
    
    if (user == null)
        return NotFound();
    
    return user;
}
```

### Service Layer
```csharp
public class UserService : IUserService
{
    private readonly ApplicationDbContext _context;
    
    public async Task<User> GetUserAsync(int id)
    {
        return await _context.Users
            .Include(u => u.Orders)
            .FirstOrDefaultAsync(u => u.Id == id);
    }
    
    public async Task CreateUserAsync(User user)
    {
        _context.Users.Add(user);
        await _context.SaveChangesAsync();
    }
}
```

## Error Handling

### Try-Catch with Async
```csharp
public async Task<Result> ProcessWithErrorHandlingAsync()
{
    try
    {
        var data = await GetDataAsync();
        return new Result { Success = true, Data = data };
    }
    catch (HttpRequestException ex)
    {
        _logger.LogError(ex, "HTTP request failed");
        return new Result { Success = false, Error = ex.Message };
    }
}
```

### Using CancellationToken
```csharp
public async Task<string> GetDataAsync(CancellationToken cancellationToken)
{
    // Check for cancellation
    cancellationToken.ThrowIfCancellationRequested();
    
    // Pass token to async operations
    var result = await _httpClient.GetStringAsync(url, cancellationToken);
    
    return result;
}
```

## Best Practices

1. **Always use async/await together** - Don't return Task directly unless performance critical
2. **Avoid async void** - Use async Task instead (except event handlers)
3. **Use ConfigureAwait(false)** in library code
4. **Pass CancellationToken** to all async methods
5. **Don't block on async code** - Never use `.Result` or `.Wait()`
6. **Name methods with Async suffix** - `GetUserAsync()` not `GetUser()`

## Anti-Patterns to Avoid

### ❌ Blocking on Async Code
```csharp
// BAD - Can cause deadlocks
var result = GetDataAsync().Result;

// GOOD
var result = await GetDataAsync();
```

### ❌ Async All the Way Down
```csharp
// BAD - Mixing sync and async
public void ProcessData()
{
    var data = GetDataAsync().Result; // Deadlock risk
}

// GOOD - Async all the way
public async Task ProcessDataAsync()
{
    var data = await GetDataAsync();
}
```

### ❌ Unnecessary Async
```csharp
// BAD - No await, just returning Task
public async Task<int> GetNumberAsync()
{
    return 42; // Warning: no await
}

// GOOD - Remove async if not awaiting
public Task<int> GetNumberAsync()
{
    return Task.FromResult(42);
}
```
