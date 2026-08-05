import { WORLD } from '../config/gameplay.js';
import { Fighter } from '../entities/Fighter.js';
import { InputController } from '../systems/InputController.js';
import { CombatSystem } from '../systems/CombatSystem.js';
import { PveController } from '../systems/PveController.js';

export class FightScene extends Phaser.Scene {
  constructor() { super('FightScene'); }

  create() {
    this.physics.world.setBounds(0, 0, WORLD.width, WORLD.height);
    this.#createStage();
    const playerFrames = this.registry.get('battleAssets')?.playerFrames;
    this.player = new Fighter(this, { id: 'player', x: 430, y: 610, texture: this.textures.exists('remote-player') ? 'remote-player' : null, frames: playerFrames, tint: 0xff4f78 });
    this.enemy = new Fighter(this, { id: 'enemy', x: 850, y: 610, texture: this.textures.exists('remote-opponent') ? 'remote-opponent' : null, tint: 0x6d5bff });
    this.physics.add.collider(this.player, this.ground);
    this.physics.add.collider(this.enemy, this.ground);
    this.physics.add.collider(this.player, this.enemy);
    this.inputController = new InputController(this);
    this.ai = new PveController(this.enemy, this.player);
    this.combat = new CombatSystem(this);
    this.combat.bind(this.player, this.enemy);
    this.scene.launch('UIScene', { player: this.player, enemy: this.enemy });
    this.player.once('defeated', () => this.#endRound('战败'));
    this.enemy.once('defeated', () => this.#endRound('胜利'));
    this.cameras.main.setBounds(0, 0, WORLD.width, WORLD.height).centerOn(WORLD.width / 2, WORLD.height / 2);
  }

  #createStage() {
    if (this.textures.exists('remote-background')) {
      this.add.image(WORLD.width / 2, WORLD.height / 2, 'remote-background').setDisplaySize(WORLD.width, WORLD.height).setDepth(-10);
    } else {
      this.add.rectangle(WORLD.width / 2, WORLD.height / 2, WORLD.width, WORLD.height, 0x171c3d).setDepth(-10);
      for (let i = 0; i < 16; i++) this.add.circle(i * 120, 500 - (i % 3) * 30, 110, i % 2 ? 0x28265a : 0x34275c, .8).setDepth(-9);
      this.add.circle(1270, 140, 120, 0xff8cb1, .85).setDepth(-9);
    }
    this.ground = this.add.rectangle(WORLD.width / 2, WORLD.floorY + 28, WORLD.width, 56, 0x11162c);
    this.physics.add.existing(this.ground, true);
    this.add.rectangle(WORLD.width / 2, WORLD.floorY, WORLD.width, 4, 0xff5f82, .65);
  }

  update(time) {
    this.player.update(time, this.inputController.read(), this.enemy);
    this.enemy.update(time, this.ai.update(time), this.player);
  }

  #endRound(label) {
    if (this.roundEnded) return;
    this.roundEnded = true;
    this.physics.pause();
    this.scene.get('UIScene').events.emit('round:end', label);
    this.time.delayedCall(2200, () => { this.scene.stop('UIScene'); this.scene.start('MenuScene'); });
  }
}
