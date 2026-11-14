using System.Text.Json;
using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class MinimalGeneratorTests
{
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(4)]
    public void GenerateWritesRequestedNumberOfEvents(int count)
    {
        using var writer = new StringWriter();
        using var errors = new StringWriter();

        var result = GeneratorCommand.Run(["generate", "--count", count.ToString()], writer, errors);

        Assert.Equal(0, result);
        Assert.Equal("", errors.ToString());
        var lines = writer.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries);
        Assert.Equal(count, lines.Length);
        foreach (var line in lines)
        {
            using var document = JsonDocument.Parse(line);
            Assert.True(document.RootElement.GetProperty("@t").TryGetDateTimeOffset(out _));
            Assert.Equal("Hello from LogLens", document.RootElement.GetProperty("@mt").GetString());
        }
        writer.Write("still open");
    }

    [Theory]
    [InlineData("generate --count -1")]
    [InlineData("generate --count abc")]
    [InlineData("generate --count 2147483648")]
    [InlineData("generate --count")]
    [InlineData("generate --unknown 2")]
    [InlineData("unknown")]
    [InlineData("generate --count 2 extra")]
    public void InvalidArgumentsFailWithoutWritingEvents(string arguments)
    {
        using var writer = new StringWriter();
        using var errors = new StringWriter();

        Assert.Equal(1, GeneratorCommand.Run(arguments.Split(' '), writer, errors));
        Assert.Equal("", writer.ToString());
        Assert.Contains("Usage:", errors.ToString());
    }

    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    public void DefaultCommandWritesOneEvent(int argumentCount)
    {
        using var writer = new StringWriter();
        using var errors = new StringWriter();
        string[] arguments = argumentCount == 0 ? [] : ["generate"];

        Assert.Equal(0, GeneratorCommand.Run(arguments, writer, errors));
        Assert.Single(writer.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries));
    }

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
        Assert.Equal(6, root.EnumerateObject().Count());
        writer.Write("still open");
    }
}
