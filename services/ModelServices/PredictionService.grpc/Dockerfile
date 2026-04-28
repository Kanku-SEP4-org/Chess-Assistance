FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
# copy csproj and restore as distinct layers
COPY services/ModelServices/PredictionService.grpc/PredictionService.grpc.csproj services/ModelServices/PredictionService.grpc/
RUN dotnet restore services/ModelServices/PredictionService.grpc/PredictionService.grpc.csproj
# copy everything else and build app
COPY services/ModelServices/PredictionService.grpc/ services/ModelServices/PredictionService.grpc/
# copy proto files
COPY shared/MAL.proto shared/

WORKDIR /src/services/ModelServices/PredictionService.grpc
RUN dotnet publish -c Release -o /app/publish
# run
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish ./
EXPOSE 5283
ENTRYPOINT ["dotnet", "PredictionService.grpc.dll"]

