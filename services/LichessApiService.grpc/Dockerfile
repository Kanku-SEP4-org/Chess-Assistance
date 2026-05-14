FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY shared/LichessApi.proto /shared/LichessApi.proto
COPY services/LichessApiService.grpc/LichessApiService.grpc.csproj ./
RUN dotnet restore

COPY services/LichessApiService.grpc/ ./
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app/publish .

EXPOSE 8082
ENV ASPNETCORE_URLS=http://+:8082

ENTRYPOINT ["dotnet", "LichessApiService.grpc.dll"]
