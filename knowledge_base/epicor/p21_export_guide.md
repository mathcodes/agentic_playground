# Epicor P21 Data Export Guide

## Overview
Epicor P21 provides multiple methods for exporting data from the ERP system. This guide covers best practices and common approaches.

## Export Methods

### 1. P21 Data Export Utility
The built-in export utility provides a GUI for exporting data:

**Steps:**
1. Navigate to System Setup > Data Export
2. Select tables/views to export
3. Choose format (CSV, XML, Excel)
4. Configure filters and scheduling
5. Specify output location

**Best Practices:**
- Use views instead of raw tables when possible
- Apply date filters to limit data volume
- Schedule exports during off-peak hours
- Validate data after export

### 2. SQL Server Integration Services (SSIS)
For automated, scheduled exports:

```sql
-- Example: Export sales data
SELECT 
    o.order_no,
    o.order_date,
    c.customer_name,
    oi.item_id,
    oi.qty_ordered,
    oi.unit_price,
    oi.extended_price
FROM 
    p21.dbo.oe_hdr o
    INNER JOIN p21.dbo.customer c ON o.customer_id = c.customer_id
    INNER JOIN p21.dbo.oe_line oi ON o.order_no = oi.order_no
WHERE 
    o.order_date >= DATEADD(day, -30, GETDATE())
ORDER BY 
    o.order_date DESC
```

**SSIS Benefits:**
- Automated scheduling
- Data transformation capabilities
- Error handling and logging
- Multiple destination formats

### 3. P21 Web Services API
For real-time exports and integrations:

```csharp
// Example: Export customer data via API
using System;
using System.Net.Http;
using System.Threading.Tasks;

public class P21ApiExporter
{
    private readonly HttpClient _client;
    private readonly string _baseUrl;
    
    public P21ApiExporter(string baseUrl, string apiKey)
    {
        _client = new HttpClient();
        _client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
        _baseUrl = baseUrl;
    }
    
    public async Task<string> ExportCustomersAsync()
    {
        var response = await _client.GetAsync($"{_baseUrl}/api/customers");
        response.EnsureSuccessStatusCode();
        return await response.ReadAsStringAsync();
    }
}
```

### 4. Direct Database Queries
For custom exports and reporting:

**Important Tables:**
- `oe_hdr` - Order headers
- `oe_line` - Order line items
- `customer` - Customer master
- `item` - Item master
- `inv_mast` - Inventory master
- `invoice_hdr` - Invoice headers
- `invoice_line` - Invoice line items

**Best Practices:**
- Use `WITH (NOLOCK)` for read-only queries
- Create indexed views for frequently exported data
- Implement proper error handling
- Log export activities

## Common Export Scenarios

### Export Sales Orders
```sql
-- Export orders from last 30 days
SELECT 
    oh.order_no,
    oh.order_date,
    oh.po_no,
    c.customer_id,
    c.customer_name,
    oh.order_total,
    oh.order_status
FROM 
    oe_hdr oh
    INNER JOIN customer c ON oh.customer_id = c.customer_id
WHERE 
    oh.order_date >= DATEADD(day, -30, GETDATE())
    AND oh.delete_flag = 'N'
ORDER BY 
    oh.order_date DESC
```

### Export Inventory Levels
```sql
-- Export current inventory by location
SELECT 
    i.item_id,
    i.item_desc,
    il.location_id,
    il.qty_on_hand,
    il.qty_allocated,
    il.qty_on_order,
    (il.qty_on_hand - il.qty_allocated) AS qty_available
FROM 
    inv_mast i
    INNER JOIN inv_loc il ON i.inv_mast_uid = il.inv_mast_uid
WHERE 
    i.delete_flag = 'N'
    AND il.qty_on_hand > 0
ORDER BY 
    i.item_id, il.location_id
```

### Export Customer Master Data
```sql
-- Export active customers with contact info
SELECT 
    c.customer_id,
    c.customer_name,
    c.phone_number,
    c.email_address,
    a.mail_address1,
    a.mail_address2,
    a.city,
    a.state_id,
    a.postal_code
FROM 
    customer c
    LEFT JOIN address a ON c.address_id = a.address_id
WHERE 
    c.delete_flag = 'N'
    AND c.active_flag = 'Y'
ORDER BY 
    c.customer_name
```

## Export Formats

### CSV (Comma-Separated Values)
- Most compatible format
- Easy to import into Excel, databases
- Limited formatting options
- Good for large datasets

### XML (Extensible Markup Language)
- Structured, hierarchical data
- Good for system integrations
- Supports complex data relationships
- Larger file sizes

### JSON (JavaScript Object Notation)
- Modern, lightweight format
- Excellent for web APIs
- Easy to parse in most languages
- Good for nested data structures

### Excel (XLSX)
- User-friendly for business users
- Supports formatting and formulas
- Limited to ~1M rows
- Slower for large datasets

## Performance Considerations

1. **Indexing**: Ensure proper indexes on filter columns
2. **Batch Processing**: Export large datasets in chunks
3. **Timing**: Schedule during off-peak hours
4. **Compression**: Compress large export files
5. **Incremental Exports**: Export only changed data when possible

## Security Best Practices

1. **Access Control**: Limit export permissions
2. **Data Masking**: Mask sensitive data (SSN, credit cards)
3. **Audit Logging**: Log all export activities
4. **Encryption**: Encrypt exported files
5. **Secure Transfer**: Use SFTP or HTTPS for file transfers

## Error Handling

```csharp
// Example: Robust export with error handling
public async Task<ExportResult> ExportDataAsync()
{
    try
    {
        // Validate connection
        if (!await ValidateConnectionAsync())
        {
            return new ExportResult 
            { 
                Success = false, 
                Error = "Database connection failed" 
            };
        }
        
        // Execute export
        var data = await FetchDataAsync();
        
        // Validate data
        if (data == null || data.Count == 0)
        {
            return new ExportResult 
            { 
                Success = false, 
                Error = "No data to export" 
            };
        }
        
        // Write to file
        await WriteToFileAsync(data);
        
        // Log success
        LogExport(data.Count);
        
        return new ExportResult 
        { 
            Success = true, 
            RecordCount = data.Count 
        };
    }
    catch (Exception ex)
    {
        LogError(ex);
        return new ExportResult 
        { 
            Success = false, 
            Error = ex.Message 
        };
    }
}
```

## Troubleshooting

### Common Issues:
1. **Timeout Errors**: Increase query timeout, add indexes
2. **Memory Issues**: Process in batches
3. **Lock Conflicts**: Use `WITH (NOLOCK)` hint
4. **Character Encoding**: Specify UTF-8 encoding
5. **Date Format Issues**: Use ISO 8601 format (YYYY-MM-DD)

## Resources
- P21 Documentation Portal
- P21 Developer Community
- SQL Server Best Practices
- Data Integration Patterns
