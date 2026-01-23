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

## Advanced Async Patterns

### ValueTask for Performance

```csharp
// Use ValueTask when result is often synchronous
public ValueTask<int> GetFromCacheAsync(string key)
{
    if (_cache.TryGetValue(key, out var value))
    {
        // Synchronous path - no allocation
        return new ValueTask<int>(value);
    }
    
    // Asynchronous path when cache miss
    return new ValueTask<int>(FetchFromDatabaseAsync(key));
}

private async Task<int> FetchFromDatabaseAsync(string key)
{
    // Actual async operation
    return await _database.GetAsync(key);
}
```

### Parallel Async Operations

```csharp
// Execute multiple async operations in parallel
public async Task<Results> GetAllDataParallelAsync()
{
    // Start all tasks
    var customersTask = GetCustomersAsync();
    var productsTask = GetProductsAsync();
    var ordersTask = GetOrdersAsync();
    
    // Wait for all to complete
    await Task.WhenAll(customersTask, productsTask, ordersTask);
    
    // Get results
    return new Results
    {
        Customers = await customersTask,
        Products = await productsTask,
        Orders = await ordersTask
    };
}

// Alternative: Collect tasks in array
public async Task<List<Customer>> GetMultipleCustomersAsync(int[] customerIds)
{
    var tasks = customerIds.Select(id => GetCustomerAsync(id)).ToArray();
    var customers = await Task.WhenAll(tasks);
    return customers.ToList();
}
```

### Progress Reporting

```csharp
// Report progress during long-running operations
public async Task<byte[]> DownloadFileAsync(
    string url,
    IProgress<int> progress,
    CancellationToken cancellationToken)
{
    using var response = await _httpClient.GetAsync(
        url,
        HttpCompletionOption.ResponseHeadersRead,
        cancellationToken
    );
    
    var totalBytes = response.Content.Headers.ContentLength ?? -1L;
    var buffer = new byte[8192];
    var totalRead = 0L;
    
    using var contentStream = await response.Content.ReadAsStreamAsync();
    using var memoryStream = new MemoryStream();
    
    int bytesRead;
    while ((bytesRead = await contentStream.ReadAsync(buffer, 0, buffer.Length, cancellationToken)) > 0)
    {
        await memoryStream.WriteAsync(buffer, 0, bytesRead, cancellationToken);
        totalRead += bytesRead;
        
        if (totalBytes > 0)
        {
            var progressPercentage = (int)((totalRead * 100) / totalBytes);
            progress?.Report(progressPercentage);
        }
    }
    
    return memoryStream.ToArray();
}

// Usage
var progress = new Progress<int>(percent =>
{
    Console.WriteLine($"Download progress: {percent}%");
});

var data = await DownloadFileAsync(url, progress, cancellationToken);
```

### Async Initialization Pattern

```csharp
// Factory method for async initialization
public class DatabaseConnection
{
    private DatabaseConnection() { }  // Private constructor
    
    public static async Task<DatabaseConnection> CreateAsync(string connectionString)
    {
        var connection = new DatabaseConnection();
        await connection.InitializeAsync(connectionString);
        return connection;
    }
    
    private async Task InitializeAsync(string connectionString)
    {
        // Async initialization logic
        await ConnectAsync(connectionString);
        await LoadConfigurationAsync();
    }
    
    private async Task ConnectAsync(string connectionString)
    {
        // Connect to database
        await Task.Delay(1000);
    }
    
    private async Task LoadConfigurationAsync()
    {
        // Load configuration
        await Task.Delay(500);
    }
}

// Usage
var connection = await DatabaseConnection.CreateAsync(connectionString);
```

### Async Lazy Initialization

```csharp
// Lazy async initialization
public class AsyncLazy<T>
{
    private readonly Lazy<Task<T>> _instance;
    
    public AsyncLazy(Func<Task<T>> factory)
    {
        _instance = new Lazy<Task<T>>(() => Task.Run(factory));
    }
    
    public Task<T> Value => _instance.Value;
}

// Usage
public class CacheService
{
    private readonly AsyncLazy<Dictionary<string, string>> _cache;
    
    public CacheService()
    {
        _cache = new AsyncLazy<Dictionary<string, string>>(LoadCacheAsync);
    }
    
    private async Task<Dictionary<string, string>> LoadCacheAsync()
    {
        // Expensive initialization
        await Task.Delay(2000);
        return new Dictionary<string, string>();
    }
    
    public async Task<string> GetAsync(string key)
    {
        var cache = await _cache.Value;
        return cache.TryGetValue(key, out var value) ? value : null;
    }
}
```

### Timeout Pattern

```csharp
// Add timeout to async operations
public async Task<T> ExecuteWithTimeoutAsync<T>(
    Func<Task<T>> operation,
    TimeSpan timeout)
{
    using var cts = new CancellationTokenSource(timeout);
    
    try
    {
        return await operation().WaitAsync(cts.Token);  // .NET 6+
    }
    catch (OperationCanceledException) when (cts.IsCancellationRequested)
    {
        throw new TimeoutException($"Operation exceeded timeout of {timeout}");
    }
}

// Pre-.NET 6 timeout pattern
public async Task<T> ExecuteWithTimeoutLegacyAsync<T>(
    Func<Task<T>> operation,
    TimeSpan timeout)
{
    var task = operation();
    var completedTask = await Task.WhenAny(task, Task.Delay(timeout));
    
    if (completedTask == task)
    {
        return await task;
    }
    else
    {
        throw new TimeoutException($"Operation exceeded timeout of {timeout}");
    }
}
```

### Retry Pattern with Exponential Backoff

```csharp
// Retry async operations with exponential backoff
public async Task<T> RetryAsync<T>(
    Func<Task<T>> operation,
    int maxRetries = 3,
    int delayMilliseconds = 1000)
{
    for (int i = 0; i < maxRetries; i++)
    {
        try
        {
            return await operation();
        }
        catch (Exception ex) when (i < maxRetries - 1)
        {
            _logger.LogWarning($"Attempt {i + 1} failed: {ex.Message}. Retrying...");
            
            // Exponential backoff
            var delay = delayMilliseconds * Math.Pow(2, i);
            await Task.Delay((int)delay);
        }
    }
    
    // Last attempt - let exception propagate
    return await operation();
}

// Usage
var result = await RetryAsync(
    async () => await _httpClient.GetStringAsync(url),
    maxRetries: 3,
    delayMilliseconds: 1000
);
```

### Async Disposal Pattern

```csharp
// Implement IAsyncDisposable for async cleanup
public class AsyncFileWriter : IAsyncDisposable
{
    private readonly Stream _stream;
    private bool _disposed;
    
    public AsyncFileWriter(string filePath)
    {
        _stream = File.OpenWrite(filePath);
    }
    
    public async Task WriteAsync(string content)
    {
        var bytes = Encoding.UTF8.GetBytes(content);
        await _stream.WriteAsync(bytes, 0, bytes.Length);
    }
    
    public async ValueTask DisposeAsync()
    {
        if (_disposed) return;
        
        // Async cleanup
        await _stream.FlushAsync();
        await _stream.DisposeAsync();
        
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}

// Usage
await using var writer = new AsyncFileWriter("output.txt");
await writer.WriteAsync("Hello, World!");
// DisposeAsync called automatically
```

### Channel Pattern for Producer-Consumer

```csharp
// Use System.Threading.Channels for async producer-consumer
public class DataProcessor
{
    private readonly Channel<string> _channel;
    
    public DataProcessor(int capacity = 100)
    {
        _channel = Channel.CreateBounded<string>(capacity);
    }
    
    // Producer
    public async Task ProduceAsync(IEnumerable<string> items, CancellationToken ct)
    {
        foreach (var item in items)
        {
            await _channel.Writer.WriteAsync(item, ct);
            await Task.Delay(100, ct);  // Simulate work
        }
        
        _channel.Writer.Complete();
    }
    
    // Consumer
    public async Task ConsumeAsync(CancellationToken ct)
    {
        await foreach (var item in _channel.Reader.ReadAllAsync(ct))
        {
            await ProcessItemAsync(item);
        }
    }
    
    private async Task ProcessItemAsync(string item)
    {
        // Process item
        await Task.Delay(50);
        Console.WriteLine($"Processed: {item}");
    }
    
    // Run both producer and consumer
    public async Task RunAsync(IEnumerable<string> items, CancellationToken ct)
    {
        var producerTask = ProduceAsync(items, ct);
        var consumerTask = ConsumeAsync(ct);
        
        await Task.WhenAll(producerTask, consumerTask);
    }
}
```

### Async Lock Pattern

```csharp
// Thread-safe async operations using SemaphoreSlim
public class AsyncCache<TKey, TValue>
{
    private readonly Dictionary<TKey, TValue> _cache = new();
    private readonly SemaphoreSlim _lock = new(1, 1);
    
    public async Task<TValue> GetOrAddAsync(
        TKey key,
        Func<TKey, Task<TValue>> valueFactory)
    {
        // First check without lock (optimistic read)
        if (_cache.TryGetValue(key, out var cachedValue))
        {
            return cachedValue;
        }
        
        // Acquire lock for write
        await _lock.WaitAsync();
        try
        {
            // Double-check after acquiring lock
            if (_cache.TryGetValue(key, out cachedValue))
            {
                return cachedValue;
            }
            
            // Generate value
            var value = await valueFactory(key);
            _cache[key] = value;
            return value;
        }
        finally
        {
            _lock.Release();
        }
    }
}
```

### Throttling Pattern

```csharp
// Limit concurrent async operations
public class AsyncThrottler
{
    private readonly SemaphoreSlim _semaphore;
    
    public AsyncThrottler(int maxConcurrency)
    {
        _semaphore = new SemaphoreSlim(maxConcurrency, maxConcurrency);
    }
    
    public async Task<T> ExecuteAsync<T>(Func<Task<T>> operation)
    {
        await _semaphore.WaitAsync();
        try
        {
            return await operation();
        }
        finally
        {
            _semaphore.Release();
        }
    }
}

// Usage: Process 100 items but only 5 at a time
var throttler = new AsyncThrottler(5);
var tasks = items.Select(item => 
    throttler.ExecuteAsync(() => ProcessItemAsync(item))
);
var results = await Task.WhenAll(tasks);
```

### Async Event Pattern

```csharp
// Async event handlers
public delegate Task AsyncEventHandler<TEventArgs>(object sender, TEventArgs e);

public class DataService
{
    public event AsyncEventHandler<DataReceivedEventArgs> DataReceived;
    
    protected virtual async Task OnDataReceivedAsync(DataReceivedEventArgs e)
    {
        var handler = DataReceived;
        if (handler != null)
        {
            // Invoke all handlers in parallel
            var delegates = handler.GetInvocationList()
                .Cast<AsyncEventHandler<DataReceivedEventArgs>>();
            
            var tasks = delegates.Select(d => d(this, e));
            await Task.WhenAll(tasks);
        }
    }
    
    public async Task ProcessDataAsync()
    {
        // Process data
        var data = await FetchDataAsync();
        
        // Raise async event
        await OnDataReceivedAsync(new DataReceivedEventArgs { Data = data });
    }
}

// Usage
dataService.DataReceived += async (sender, e) =>
{
    await SaveToFileAsync(e.Data);
};

dataService.DataReceived += async (sender, e) =>
{
    await SendNotificationAsync(e.Data);
};
```

## Testing Async Code

### Unit Testing Async Methods

```csharp
[Fact]
public async Task GetCustomerAsync_ReturnsCustomer_WhenExists()
{
    // Arrange
    var customerId = 123;
    var expectedCustomer = new Customer { CustomerId = customerId, Name = "Test" };
    _mockRepository.Setup(r => r.GetAsync(customerId))
        .ReturnsAsync(expectedCustomer);
    
    // Act
    var result = await _service.GetCustomerAsync(customerId);
    
    // Assert
    Assert.NotNull(result);
    Assert.Equal(expectedCustomer.Name, result.Name);
}

[Fact]
public async Task ProcessAsync_ThrowsException_OnError()
{
    // Arrange
    _mockRepository.Setup(r => r.SaveAsync(It.IsAny<Customer>()))
        .ThrowsAsync(new DbUpdateException());
    
    // Act & Assert
    await Assert.ThrowsAsync<DbUpdateException>(
        () => _service.ProcessAsync(new Customer())
    );
}
```

### Testing with Cancellation

```csharp
[Fact]
public async Task ProcessAsync_CancelsCorrectly_WhenTokenCancelled()
{
    // Arrange
    var cts = new CancellationTokenSource();
    var task = _service.LongRunningProcessAsync(cts.Token);
    
    // Act
    cts.Cancel();
    
    // Assert
    await Assert.ThrowsAsync<OperationCanceledException>(() => task);
}
```

## Async Best Practices Extended

Architecture:
- [ ] Use async all the way down - don't mix sync and async
- [ ] Return Task<T> instead of void (except event handlers)
- [ ] Use ValueTask<T> for hot paths with often-synchronous results
- [ ] Consider IAsyncEnumerable<T> for streaming data

Error Handling:
- [ ] Always use try-catch with async operations
- [ ] Don't swallow exceptions
- [ ] Log exceptions appropriately
- [ ] Use AggregateException handling with Task.WhenAll

Cancellation:
- [ ] Always accept CancellationToken in async methods
- [ ] Check for cancellation in long-running loops
- [ ] Pass cancellation tokens to underlying async calls
- [ ] Handle OperationCanceledException appropriately

Performance:
- [ ] Avoid unnecessary Task allocation
- [ ] Use ValueTask for synchronous fast paths
- [ ] Don't use async for purely CPU-bound work
- [ ] Consider using Task.Run for CPU-bound work in UI apps

Testing:
- [ ] Test both successful and failure paths
- [ ] Test cancellation scenarios
- [ ] Test timeout scenarios
- [ ] Use async test frameworks (xUnit, NUnit async)

Monitoring:
- [ ] Log async operation start and completion
- [ ] Track async operation performance
- [ ] Monitor for deadlocks
- [ ] Use diagnostic tools (async stack traces, ETW)
