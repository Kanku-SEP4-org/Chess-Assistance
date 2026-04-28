FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Restore dependencies first (layer cache)
COPY services/grpc-service/GrpcService.csproj services/grpc-service/
RUN dotnet restore services/grpc-service/GrpcService.csproj

# Copy project source and shared proto files
COPY services/grpc-service/ services/grpc-service/
COPY shared/ shared/

WORKDIR /src/services/grpc-service
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish ./
EXPOSE 50051
ENTRYPOINT ["dotnet", "GrpcService.dll"]
