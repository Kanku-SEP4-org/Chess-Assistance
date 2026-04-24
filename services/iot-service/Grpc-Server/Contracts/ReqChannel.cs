using System;
using RabbitMQ.Client;

namespace Grpc_Server.Contracts;

public sealed class ReqChannel { public IChannel Channel { get; } public ReqChannel(IChannel m) => Channel = m; }
