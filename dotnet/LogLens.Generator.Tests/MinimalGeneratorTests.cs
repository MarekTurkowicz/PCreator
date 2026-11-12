using System.Text.Json;
using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class MinimalGeneratorTests
{
    [Fact]
    public void WritesOneMinimalClefEventAndKeepsWriterOpen()
    {
        using var writer = new StringWriter();

        MinimalGenerator.Write(writer);

        var lines = writer.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries);
        var line = Assert.Single(lines);
        using var document = JsonDocument.Parse(line);
        var root = document.RootElement;
        Assert.True(root.GetProperty("@t").TryGetDateTimeOffset(out _));
        Assert.Equal("Hello from LogLens", root.GetProperty("@mt").GetString());
        Assert.False(root.TryGetProperty("@l", out _));
        Assert.Equal(2, root.EnumerateObject().Count());
        writer.Write("still open");
    }
}
