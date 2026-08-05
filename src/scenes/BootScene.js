import { createBattleAssets } from '../services/AnimeGanService.js';

export class BootScene extends Phaser.Scene {
  constructor() { super('BootScene'); }

  init() {
    const query = new URLSearchParams(location.search);
    const saved = JSON.parse(sessionStorage.getItem('generatedBattleAssets') || '{}');
    this.assets = createBattleAssets({
      playerUrl: query.get('player') || window.__BATTLE_ASSETS__?.playerUrl || saved.playerUrl,
      opponentUrl: query.get('opponent') || window.__BATTLE_ASSETS__?.opponentUrl || saved.opponentUrl,
      backgroundUrl: query.get('background') || window.__BATTLE_ASSETS__?.backgroundUrl || saved.backgroundUrl,
      playerFrames: saved.playerFrames,
      gameId: saved.gameId,
      gameConfig: saved.gameConfig,
      obstacles: saved.obstacles,
      coin: saved.coin,
    });
  }

  preload() {
    const { playerUrl, opponentUrl, backgroundUrl } = this.assets;
    if (playerUrl) this.load.image('remote-player', playerUrl);
    if (opponentUrl) this.load.image('remote-opponent', opponentUrl);
    if (backgroundUrl) this.load.image('remote-background', backgroundUrl);
    this.assets.playerFrames?.run?.forEach((url, index) => this.load.image(`remote-player-run-${index}`, url));
    if (this.assets.playerFrames?.jump) this.load.image('remote-player-jump', this.assets.playerFrames.jump);
    this.load.on('loaderror', (file) => console.warn(`远程素材加载失败，使用占位素材: ${file.src}`));
  }

  create() {
    this.registry.set('battleAssets', this.assets);
    this.scene.start('MenuScene');
  }
}
