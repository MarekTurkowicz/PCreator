---
name: dotnet-serilog
description: Część C#/.NET 8 projektu LogLens — struktura dotnet/, generator logów Serilog CLEF, testy xUnit. Użyj przy krokach dotyczących C#.
---

# .NET w LogLens

## Struktura
```
dotnet/LogLens.sln
dotnet/LogLens.Generator/        # console app: generuje logi CLEF
dotnet/LogLens.Generator.Tests/  # xUnit
```
Tworzenie: `dotnet new sln -n LogLens -o dotnet`, `dotnet new console -n LogLens.Generator -o dotnet/LogLens.Generator`,
`dotnet new xunit -n LogLens.Generator.Tests -o dotnet/LogLens.Generator.Tests`, potem `dotnet sln add`.
Target: `net8.0`, `<Nullable>enable</Nullable>`, `<ImplicitUsings>enable</ImplicitUsings>`.

## Pakiety
Dopisuj ręcznie do `.csproj` (sandbox nie ma sieci, `dotnet add package` nie zadziała):
`Serilog`, `Serilog.Formatting.Compact`, `Serilog.Sinks.File`. Restore zrobi skrypt poza sandboxem.

## Format CLEF (kontrakt z Pythonem)
Jedna linia = jeden JSON: `@t` (ISO 8601), `@mt` (szablon), `@l` (poziom; brak = Information),
`@x` (wyjątek), dalej właściwości, np. `RequestPath`, `StatusCode`, `Elapsed`.
Generator musi być deterministyczny dla `--seed`, żeby testy po obu stronach były stabilne.

## Testy
Testuj logikę generatora (rozkład błędów, poprawność JSON), a nie samego Seriloga.
Zapis do `MemoryStream`/`StringWriter` zamiast plików.
