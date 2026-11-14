using System.Text.Json;
using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class HttpContextTests
{
    [Theory]
    [InlineData(null)]
    [InlineData(42)]
    [InlineData(-1)]
    public void EventsContainHttpContextWithinDocumentedRanges(int? seed)
    {
        using var output = new StringWriter();
        MinimalGenerator.Write(output, 100, seed);
        var lines = output.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries);
        Assert.Equal(100, lines.Length);
        foreach (var line in lines)
        {
            using var document = JsonDocument.Parse(line);
            var root = document.RootElement;
            Assert.Contains(root.GetProperty("RequestPath").GetString(),
                new[] { "/api/orders", "/api/products", "/health" });
            Assert.Equal("GET", root.GetProperty("RequestMethod").GetString());
            Assert.Equal(200, root.GetProperty("StatusCode").GetInt32());
            Assert.InRange(root.GetProperty("Elapsed").GetDouble(), 0.1, 500.0);
        }
    }
}
