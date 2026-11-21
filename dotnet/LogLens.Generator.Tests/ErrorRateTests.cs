using System.Text.Json;
using LogLens.Generator;
using Xunit;

namespace LogLens.Generator.Tests;

public class ErrorRateTests
{
    private static string Generate(string rate, string count = "100")
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(0, GeneratorCommand.Run(
            ["generate", "--error-rate", rate, "--seed", "42", "--count", count], output, error));
        Assert.Equal("", error.ToString());
        return output.ToString();
    }

    [Theory]
    [InlineData("0", false)]
    [InlineData("1", true)]
    public void BoundaryRatesProduceOnlyExpectedEvents(string rate, bool failed)
    {
        var lines = Generate(rate).Split('\n', StringSplitOptions.RemoveEmptyEntries);
        Assert.Equal(100, lines.Length);
        foreach (var line in lines)
        {
            using var document = JsonDocument.Parse(line);
            var root = document.RootElement;
            Assert.Equal(failed ? 500 : 200, root.GetProperty("StatusCode").GetInt32());
            Assert.Equal(failed, root.TryGetProperty("@x", out var exception));
            if (failed)
            {
                Assert.Equal("Error", root.GetProperty("@l").GetString());
                Assert.Equal("System.InvalidOperationException: Request failed", exception.GetString());
            }
            else
            {
                Assert.False(root.TryGetProperty("@l", out _));
            }
        }
    }

    [Fact]
    public void Seed42ErrorMatchesPythonSample()
    {
        using var document = JsonDocument.Parse(Generate("1", "1"));
        var root = document.RootElement;
        Assert.Equal(new DateTimeOffset(1970, 1, 1, 16, 2, 4, TimeSpan.Zero),
            root.GetProperty("@t").GetDateTimeOffset());
        Assert.Equal("/api/orders", root.GetProperty("RequestPath").GetString());
        Assert.Equal("GET", root.GetProperty("RequestMethod").GetString());
        Assert.Equal(62.8, root.GetProperty("Elapsed").GetDouble());
    }

    [Fact]
    public void FractionalRateIsRepeatableAndProducesBothOutcomes()
    {
        var output = Generate("0.5");
        Assert.Equal(output, Generate("0.5"));
        var errors = output.Split('\n').Count(line => line.Contains("\"@x\""));
        Assert.InRange(errors, 1, 99);
        Assert.Equal("", Generate("1", "0"));
    }

    [Theory]
    [InlineData("generate --error-rate")]
    [InlineData("generate --error-rate -0.1")]
    [InlineData("generate --error-rate 1.1")]
    [InlineData("generate --error-rate NaN")]
    [InlineData("generate --error-rate Infinity")]
    [InlineData("generate --error-rate abc")]
    [InlineData("generate --error-rate 0,5")]
    [InlineData("generate --error-rate 0 --error-rate 1")]
    public void InvalidRateWritesNoEvents(string arguments)
    {
        using var output = new StringWriter();
        using var error = new StringWriter();
        Assert.Equal(1, GeneratorCommand.Run(arguments.Split(' '), output, error));
        Assert.Equal("", output.ToString());
        Assert.Contains("Usage:", error.ToString());
    }

    [Theory]
    [InlineData(-0.1)]
    [InlineData(1.1)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public void DirectApiRejectsInvalidRate(double rate)
    {
        using var output = new StringWriter();
        Assert.Throws<ArgumentOutOfRangeException>(() =>
            MinimalGenerator.Write(output, errorRate: rate));
        Assert.Equal("", output.ToString());
    }
}
