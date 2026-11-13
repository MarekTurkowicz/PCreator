using System.Text.Json;
using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class SeedTests
{
    private static string Generate(params string[] args)
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(0, GeneratorCommand.Run(args, output, error));
        Assert.Equal("", error.ToString());
        return output.ToString();
    }

    [Theory]
    [InlineData("0")]
    [InlineData("42")]
    [InlineData("-2147483648")]
    [InlineData("2147483647")]
    public void SeedReproducesCompleteClefInEitherOptionOrder(string seed)
    {
        var first = Generate("generate", "--count", "3", "--seed", seed);
        var second = Generate("generate", "--seed", seed, "--count", "3");

        Assert.Equal(first, second);
        var lines = first.Split('\n', StringSplitOptions.RemoveEmptyEntries);
        Assert.Equal(3, lines.Length);
        foreach (var line in lines)
        {
            using var document = JsonDocument.Parse(line);
            Assert.True(document.RootElement.GetProperty("@t").TryGetDateTimeOffset(out _));
            Assert.Equal("Hello from LogLens", document.RootElement.GetProperty("@mt").GetString());
        }
    }

    [Fact]
    public void DifferentSeedsChangeOutput()
    {
        Assert.NotEqual(Generate("generate", "--seed", "1"), Generate("generate", "--seed", "2"));
    }

    [Fact]
    public void Seed42MatchesPythonSampleTimestamps()
    {
        var lines = Generate("generate", "--count", "3", "--seed", "42")
            .Split('\n', StringSplitOptions.RemoveEmptyEntries);
        var start = new DateTimeOffset(1970, 1, 1, 16, 2, 4, TimeSpan.Zero);
        for (var index = 0; index < lines.Length; index++)
        {
            using var document = JsonDocument.Parse(lines[index]);
            Assert.Equal(start.AddMilliseconds(index),
                document.RootElement.GetProperty("@t").GetDateTimeOffset());
        }
    }

    [Fact]
    public void SeedSupportsDefaultAndZeroCount()
    {
        Assert.Single(Generate("generate", "--seed", "42").Split('\n', StringSplitOptions.RemoveEmptyEntries));
        Assert.Equal("", Generate("generate", "--seed", "42", "--count", "0"));
    }

    [Theory]
    [InlineData("generate --seed")]
    [InlineData("generate --seed abc")]
    [InlineData("generate --seed 2147483648")]
    [InlineData("generate --seed -2147483649")]
    [InlineData("generate --seed 1 --seed 2")]
    [InlineData("generate --count 1 --count 2")]
    [InlineData("generate --seed 1 --count -1")]
    public void InvalidOptionsWriteNoEvents(string arguments)
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(1, GeneratorCommand.Run(arguments.Split(' '), output, error));
        Assert.Equal("", output.ToString());
        Assert.Contains("Usage:", error.ToString());
    }
}
