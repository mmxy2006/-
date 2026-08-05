// PVP 边界：FightScene 只依赖这些事件，后续可将空实现换成 WebSocket。
export class MultiplayerGateway extends EventTarget {
  connect() { throw new Error('PVP gateway is reserved for the next milestone'); }
  sendInput(_frameInput) {}
  disconnect() {}
}
