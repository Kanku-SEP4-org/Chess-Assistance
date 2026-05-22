using System;
using RabbitMQ.Client;

namespace Grpc_Server.Contracts;

public sealed class ResChannel { public IChannel Channel { get; } public ResChannel(IChannel m) => Channel = m; }
