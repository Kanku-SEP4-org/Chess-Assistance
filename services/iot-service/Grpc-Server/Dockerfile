FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["Grpc-Server/Grpc-Server.csproj", "Grpc-Server/"]
RUN dotnet restore "Grpc-Server/Grpc-Server.csproj"

COPY . .
WORKDIR "/src/Grpc-Server"

RUN dotnet publish "Grpc-Server.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080

ENTRYPOINT ["dotnet", "Grpc-Server.dll"]