export class UIScene extends Phaser.Scene {
  constructor() { super('UIScene'); }

  create({ player, enemy }) {
    this.#makeHealthBar(70, 54, false, 'PLAYER', player, 0xf5ae36);
    this.#makeHealthBar(1210, 54, true, 'CPU', enemy, 0xe78042);
    this.add.text(640, 62, '∞', { fontSize: 42, fontStyle: 'bold', color: '#71441f' }).setOrigin(.5);
    this.add.text(640, 112, 'PVE · ROUND 1', { fontSize: 14, color: '#795538', letterSpacing: 3 }).setOrigin(.5);
    this.add.text(32, 675, 'J 普攻   Q 突进斩   E 升龙   R 能量弹', { fontSize: 15, color: '#fffaf0', backgroundColor: '#8a572dcc', padding: { x: 12, y: 8 } });
    this.events.on('round:end', (label, score) => {
      this.add.rectangle(640, 350, 520, 150, 0x7a4b24, .9).setStrokeStyle(4, 0xffe09a, .85);
      this.add.text(640, 330, label, { fontFamily: 'Arial Black', fontSize: 62, color: label === '胜利' ? '#ffe28d' : '#fffaf0' }).setOrigin(.5);
      this.add.text(640, 395, `本局得分  ${score}`, { fontSize: 22, color: '#fff5d2', fontStyle: 'bold' }).setOrigin(.5);
    });
  }

  #makeHealthBar(x, y, flipped, name, fighter, color) {
    const width = 440;
    this.add.text(flipped ? x - width : x, y - 30, name, { fontSize: 16, fontStyle: 'bold', color: '#68401f' }).setOrigin(0, .5);
    const bg = this.add.rectangle(x, y, width, 26, 0xfff0bd).setOrigin(flipped ? 1 : 0, .5).setStrokeStyle(3, 0x8b5a2b, .75);
    const bar = this.add.rectangle(x, y, width - 8, 18, color).setOrigin(flipped ? 1 : 0, .5);
    fighter.on('healthChanged', (ratio) => this.tweens.add({ targets: bar, displayWidth: (width - 8) * ratio, duration: 260, ease: 'Cubic.Out' }));
    return { bg, bar };
  }
}
