export class MenuScene extends Phaser.Scene {
  constructor() { super('MenuScene'); }

  create() {
    this.cameras.main.setBackgroundColor('#10162f');
    this.add.circle(1050, 150, 330, 0x8f4cff, .15);
    this.add.circle(180, 600, 300, 0xff416c, .12);
    this.add.text(640, 220, 'AI CARTOON', { fontFamily: 'Arial Black', fontSize: 38, color: '#ff6f91', letterSpacing: 8 }).setOrigin(.5);
    this.add.text(640, 290, 'FIGHTER', { fontFamily: 'Arial Black', fontSize: 92, color: '#ffffff', stroke: '#6b36db', strokeThickness: 8 }).setOrigin(.5);
    this.add.text(640, 390, '上传照片生成你的专属格斗角色', { fontSize: 20, color: '#bfc7e8' }).setOrigin(.5);
    const button = this.add.rectangle(640, 490, 280, 68, 0xff5477).setInteractive({ useHandCursor: true });
    this.add.text(640, 490, '开始 PVE 对战', { fontSize: 24, fontStyle: 'bold' }).setOrigin(.5);
    button.on('pointerover', () => button.setFillStyle(0xff7894));
    button.on('pointerout', () => button.setFillStyle(0xff5477));
    button.on('pointerdown', () => this.scene.start('FightScene'));
    this.input.keyboard.once('keydown-ENTER', () => this.scene.start('FightScene'));
    this.add.text(640, 560, 'ENTER 快速开始', { fontSize: 14, color: '#7e86aa' }).setOrigin(.5);
    this.game.events.on('assets:generated', this.loadGeneratedAssets, this);
    this.events.once('shutdown', () => this.game.events.off('assets:generated', this.loadGeneratedAssets, this));
  }

  loadGeneratedAssets(assets) {
    this.registry.set('battleAssets', assets);
    const queue = [];
    if (assets.playerUrl) queue.push(['remote-player', assets.playerUrl]);
    if (assets.backgroundUrl) queue.push(['remote-background', assets.backgroundUrl]);
    assets.playerFrames?.run?.forEach((url, index) => queue.push([`remote-player-run-${index}`, url]));
    if (assets.playerFrames?.jump) queue.push(['remote-player-jump', assets.playerFrames.jump]);
    for (const [key, url] of queue) {
      if (this.textures.exists(key)) this.textures.remove(key);
      this.load.image(key, url);
    }
    if (!queue.length) return this.scene.start('FightScene');
    this.load.once('complete', () => this.scene.start('FightScene'));
    this.load.once('loaderror', (file) => console.error('生成素材载入失败', file.src));
    this.load.start();
  }
}
