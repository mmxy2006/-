import { WORLD } from '../config/gameplay.js';
import { Fighter } from '../entities/Fighter.js';
import { InputController } from '../systems/InputController.js';
import { CombatSystem } from '../systems/CombatSystem.js';
import { PveController } from '../systems/PveController.js';

export class FightScene extends Phaser.Scene {
  constructor() { super('FightScene'); }

  create() {
    const query = new URLSearchParams(location.search);
    this.nickname = (query.get('nickname') || localStorage.getItem('fighterNickname') || '匿名勇士').trim().slice(0, 16) || '匿名勇士';
    this.difficulty = ['easy', 'normal', 'hard'].includes(query.get('difficulty')) ? query.get('difficulty') : 'normal';
    this.physics.world.setBounds(0, 0, WORLD.width, WORLD.height);
    this.#createStage();
    const playerFrames = this.registry.get('battleAssets')?.playerFrames;
    this.player = new Fighter(this, { id: 'player', x: 430, y: 610, texture: this.textures.exists('remote-player') ? 'remote-player' : null, frames: playerFrames, tint: 0xf0aa3c });
    this.enemy = new Fighter(this, { id: 'enemy', x: 850, y: 610, texture: this.textures.exists('remote-opponent') ? 'remote-opponent' : null, tint: 0xe48745 });
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
      this.add.rectangle(WORLD.width / 2, WORLD.height / 2, WORLD.width, WORLD.height, 0xfff0b8).setDepth(-10);
      for (let i = 0; i < 16; i++) this.add.circle(i * 120, 500 - (i % 3) * 30, 110, i % 2 ? 0xf6cf75 : 0xffdf8f, .8).setDepth(-9);
      this.add.circle(1270, 140, 120, 0xffc95d, .8).setDepth(-9);
    }
    this.add.rectangle(WORLD.width / 2, WORLD.height / 2, WORLD.width, WORLD.height, 0xffe59b, .08).setDepth(-8);
    this.ground = this.add.rectangle(WORLD.width / 2, WORLD.floorY + 28, WORLD.width, 56, 0x9b6a38);
    this.physics.add.existing(this.ground, true);
    this.add.rectangle(WORLD.width / 2, WORLD.floorY, WORLD.width, 4, 0xffd36b, .9);
  }

  update(time) {
    this.player.update(time, this.inputController.read(), this.enemy);
    this.enemy.update(time, this.ai.update(time), this.player);
  }

  #endRound(label) {
    if (this.roundEnded) return;
    this.roundEnded = true;
    this.physics.pause();
    const won = label === '胜利';
    const damageScore = Math.round((100 - this.enemy.health) * 6);
    const survivalScore = Math.round(this.player.health * 4);
    const score = Math.max(0, damageScore + survivalScore + (won ? 1000 : 0));
    this.scene.get('UIScene').events.emit('round:end', label, score);
    this.#submitScore(score);
    this.time.delayedCall(2200, () => { this.scene.stop('UIScene'); this.scene.start('MenuScene'); });
  }

  async #submitScore(score) {
    const gameId = this.registry.get('battleAssets')?.gameId || null;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/games/scores', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: this.nickname, score, difficulty: this.difficulty, game_id: gameId }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const entry = await response.json();
      window.parent?.postMessage({ type: 'fighter:score-submitted', entry }, location.origin);
    } catch (error) {
      console.warn('排行榜成绩提交失败', error);
    }
  }
}
