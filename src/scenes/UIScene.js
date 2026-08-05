export class UIScene extends Phaser.Scene {
  constructor() { super('UIScene'); }

  create({ player, enemy }) {
    this.#makeHealthBar(70, 54, false, 'PLAYER', player, 0xff5578);
    this.#makeHealthBar(1210, 54, true, 'CPU', enemy, 0x7668ff);
    this.add.text(640, 62, '∞', { fontSize: 42, fontStyle: 'bold' }).setOrigin(.5);
    this.add.text(640, 112, 'PVE · ROUND 1', { fontSize: 14, color: '#c5cbe5', letterSpacing: 3 }).setOrigin(.5);
    this.add.text(32, 675, 'J 普攻   Q 突进斩   E 升龙   R 能量弹', { fontSize: 15, color: '#d6daed', backgroundColor: '#080b18aa', padding: { x: 12, y: 8 } });
    this.events.on('round:end', (label) => {
      this.add.rectangle(640, 350, 520, 150, 0x070916, .88);
      this.add.text(640, 350, label, { fontFamily: 'Arial Black', fontSize: 72, color: label === '胜利' ? '#ffdc73' : '#ffffff' }).setOrigin(.5);
    });
  }

  #makeHealthBar(x, y, flipped, name, fighter, color) {
    const width = 440;
    this.add.text(flipped ? x - width : x, y - 30, name, { fontSize: 16, fontStyle: 'bold' }).setOrigin(flipped ? 0 : 0, .5);
    const bg = this.add.rectangle(x, y, width, 26, 0x22263c).setOrigin(flipped ? 1 : 0, .5).setStrokeStyle(3, 0xffffff, .7);
    const bar = this.add.rectangle(x, y, width - 8, 18, color).setOrigin(flipped ? 1 : 0, .5);
    fighter.on('healthChanged', (ratio) => this.tweens.add({ targets: bar, displayWidth: (width - 8) * ratio, duration: 260, ease: 'Cubic.Out' }));
    return { bg, bar };
  }
}
