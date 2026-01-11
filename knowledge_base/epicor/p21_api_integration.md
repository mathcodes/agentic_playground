# Epicor P21 API Integration Guide

## Overview
The Epicor P21 Web Services API provides RESTful endpoints for integrating with the P21 ERP system. This guide covers authentication, common operations, and best practices.

## API Architecture

### Base URL
```
https://your-p21-server.com/p21api/v1/
```

### Authentication
P21 API uses OAuth 2.0 for authentication:

```csharp
public class P21AuthService
{
    private readonly HttpClient _client;
    private string _accessToken;
    private DateTime _tokenExpiry;
    
    public async Task<string> GetAccessTokenAsync(
        string clientId, 
        string clientSecret)
    {
        // Check if token is still valid
        if (!string.IsNullOrEmpty(_accessToken) && 
            DateTime.UtcNow < _tokenExpiry)
        {
            return _accessToken;
        }
        
        // Request new token
        var request = new HttpRequestMessage(HttpMethod.Post, "oauth/token");
        var content = new FormUrlEncodedContent(new[]
        {
            new KeyValuePair<string, string>("grant_type", "client_credentials"),
            new KeyValuePair<string, string>("client_id", clientId),
            new KeyValuePair<string, string>("client_secret", clientSecret)
        });
        
        request.Content = content;
        var response = await _client.SendAsync(request);
        response.EnsureSuccessStatusCode();
        
        var result = await response.Content.ReadAsAsync<TokenResponse>();
        _accessToken = result.AccessToken;
        _tokenExpiry = DateTime.UtcNow.AddSeconds(result.ExpiresIn - 60);
        
        return _accessToken;
    }
}
```

## Common API Operations

### 1. Customer Operations

#### Get Customer by ID
```csharp
public async Task<Customer> GetCustomerAsync(string customerId)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var response = await _client.GetAsync($"customers/{customerId}");
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<Customer>();
}
```

#### Create Customer
```csharp
public async Task<Customer> CreateCustomerAsync(CustomerCreateRequest request)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var response = await _client.PostAsJsonAsync("customers", request);
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<Customer>();
}
```

#### Update Customer
```csharp
public async Task<Customer> UpdateCustomerAsync(
    string customerId, 
    CustomerUpdateRequest request)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var response = await _client.PutAsJsonAsync(
        $"customers/{customerId}", 
        request);
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<Customer>();
}
```

### 2. Order Operations

#### Get Orders
```csharp
public async Task<List<Order>> GetOrdersAsync(
    DateTime? startDate = null,
    DateTime? endDate = null,
    int pageSize = 100,
    int pageNumber = 1)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var queryParams = new Dictionary<string, string>
    {
        ["pageSize"] = pageSize.ToString(),
        ["pageNumber"] = pageNumber.ToString()
    };
    
    if (startDate.HasValue)
        queryParams["startDate"] = startDate.Value.ToString("yyyy-MM-dd");
    if (endDate.HasValue)
        queryParams["endDate"] = endDate.Value.ToString("yyyy-MM-dd");
    
    var query = string.Join("&", 
        queryParams.Select(kvp => $"{kvp.Key}={kvp.Value}"));
    
    var response = await _client.GetAsync($"orders?{query}");
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<List<Order>>();
}
```

#### Create Order
```csharp
public async Task<Order> CreateOrderAsync(OrderCreateRequest request)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var response = await _client.PostAsJsonAsync("orders", request);
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<Order>();
}
```

### 3. Inventory Operations

#### Get Item Information
```csharp
public async Task<Item> GetItemAsync(string itemId)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var response = await _client.GetAsync($"items/{itemId}");
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<Item>();
}
```

#### Get Inventory Levels
```csharp
public async Task<List<InventoryLevel>> GetInventoryLevelsAsync(
    string itemId,
    string locationId = null)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var url = $"inventory/{itemId}";
    if (!string.IsNullOrEmpty(locationId))
        url += $"?locationId={locationId}";
    
    var response = await _client.GetAsync(url);
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<List<InventoryLevel>>();
}
```

### 4. Invoice Operations

#### Get Invoices
```csharp
public async Task<List<Invoice>> GetInvoicesAsync(
    string customerId = null,
    DateTime? startDate = null,
    DateTime? endDate = null)
{
    var token = await _authService.GetAccessTokenAsync();
    _client.DefaultRequestHeaders.Authorization = 
        new AuthenticationHeaderValue("Bearer", token);
    
    var queryParams = new List<string>();
    if (!string.IsNullOrEmpty(customerId))
        queryParams.Add($"customerId={customerId}");
    if (startDate.HasValue)
        queryParams.Add($"startDate={startDate.Value:yyyy-MM-dd}");
    if (endDate.HasValue)
        queryParams.Add($"endDate={endDate.Value:yyyy-MM-dd}");
    
    var query = queryParams.Any() ? "?" + string.Join("&", queryParams) : "";
    
    var response = await _client.GetAsync($"invoices{query}");
    response.EnsureSuccessStatusCode();
    
    return await response.Content.ReadAsAsync<List<Invoice>>();
}
```

## Best Practices

### 1. Connection Management
```csharp
public class P21ApiClient : IDisposable
{
    private readonly HttpClient _client;
    private readonly P21AuthService _authService;
    
    public P21ApiClient(string baseUrl, string clientId, string clientSecret)
    {
        _client = new HttpClient
        {
            BaseAddress = new Uri(baseUrl),
            Timeout = TimeSpan.FromSeconds(30)
        };
        
        _authService = new P21AuthService(_client, clientId, clientSecret);
    }
    
    public void Dispose()
    {
        _client?.Dispose();
    }
}
```

### 2. Retry Logic with Polly
```csharp
using Polly;
using Polly.Extensions.Http;

public static IAsyncPolicy<HttpResponseMessage> GetRetryPolicy()
{
    return HttpPolicyExtensions
        .HandleTransientHttpError()
        .OrResult(msg => msg.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
        .WaitAndRetryAsync(3, retryAttempt => 
            TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));
}

// Usage
var response = await GetRetryPolicy()
    .ExecuteAsync(() => _client.GetAsync("customers"));
```

### 3. Rate Limiting
```csharp
public class RateLimiter
{
    private readonly SemaphoreSlim _semaphore;
    private readonly int _maxRequestsPerSecond;
    private DateTime _lastResetTime;
    private int _requestCount;
    
    public RateLimiter(int maxRequestsPerSecond)
    {
        _maxRequestsPerSecond = maxRequestsPerSecond;
        _semaphore = new SemaphoreSlim(1, 1);
        _lastResetTime = DateTime.UtcNow;
    }
    
    public async Task WaitAsync()
    {
        await _semaphore.WaitAsync();
        try
        {
            var now = DateTime.UtcNow;
            if ((now - _lastResetTime).TotalSeconds >= 1)
            {
                _requestCount = 0;
                _lastResetTime = now;
            }
            
            if (_requestCount >= _maxRequestsPerSecond)
            {
                var delay = 1000 - (int)(now - _lastResetTime).TotalMilliseconds;
                if (delay > 0)
                    await Task.Delay(delay);
                
                _requestCount = 0;
                _lastResetTime = DateTime.UtcNow;
            }
            
            _requestCount++;
        }
        finally
        {
            _semaphore.Release();
        }
    }
}
```

### 4. Error Handling
```csharp
public async Task<ApiResult<T>> SafeApiCallAsync<T>(
    Func<Task<HttpResponseMessage>> apiCall)
{
    try
    {
        var response = await apiCall();
        
        if (response.IsSuccessStatusCode)
        {
            var data = await response.Content.ReadAsAsync<T>();
            return ApiResult<T>.Success(data);
        }
        
        var error = await response.Content.ReadAsStringAsync();
        return ApiResult<T>.Failure(
            $"API Error: {response.StatusCode} - {error}");
    }
    catch (HttpRequestException ex)
    {
        return ApiResult<T>.Failure($"Network Error: {ex.Message}");
    }
    catch (TaskCanceledException ex)
    {
        return ApiResult<T>.Failure($"Timeout: {ex.Message}");
    }
    catch (Exception ex)
    {
        return ApiResult<T>.Failure($"Unexpected Error: {ex.Message}");
    }
}
```

### 5. Logging
```csharp
public class LoggingHandler : DelegatingHandler
{
    private readonly ILogger _logger;
    
    public LoggingHandler(ILogger logger)
    {
        _logger = logger;
    }
    
    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Request: {Method} {Url}", 
            request.Method, 
            request.RequestUri);
        
        var sw = Stopwatch.StartNew();
        var response = await base.SendAsync(request, cancellationToken);
        sw.Stop();
        
        _logger.LogInformation(
            "Response: {StatusCode} in {ElapsedMs}ms",
            response.StatusCode,
            sw.ElapsedMilliseconds);
        
        return response;
    }
}
```

## Common Scenarios

### Bulk Data Sync
```csharp
public async Task SyncCustomersAsync()
{
    var pageNumber = 1;
    var pageSize = 100;
    var hasMore = true;
    
    while (hasMore)
    {
        var customers = await GetCustomersAsync(pageSize, pageNumber);
        
        if (customers.Count == 0)
        {
            hasMore = false;
        }
        else
        {
            await ProcessCustomersAsync(customers);
            pageNumber++;
        }
    }
}
```

### Real-time Integration
```csharp
public async Task<Order> CreateOrderFromWebAsync(WebOrder webOrder)
{
    // Map web order to P21 format
    var p21Order = new OrderCreateRequest
    {
        CustomerId = webOrder.CustomerId,
        OrderDate = DateTime.UtcNow,
        Lines = webOrder.Items.Select(item => new OrderLine
        {
            ItemId = item.Sku,
            Quantity = item.Quantity,
            UnitPrice = item.Price
        }).ToList()
    };
    
    // Create in P21
    var result = await CreateOrderAsync(p21Order);
    
    // Update web system with P21 order number
    await UpdateWebOrderAsync(webOrder.Id, result.OrderNo);
    
    return result;
}
```

## Troubleshooting

### Common Issues:
1. **401 Unauthorized**: Check API credentials and token expiry
2. **429 Too Many Requests**: Implement rate limiting
3. **500 Server Error**: Check P21 server logs, validate request data
4. **Timeout**: Increase timeout, optimize query parameters
5. **SSL/TLS Errors**: Update certificates, check server configuration

## Resources
- P21 API Documentation
- OAuth 2.0 Specification
- RESTful API Best Practices
- C# HttpClient Best Practices
