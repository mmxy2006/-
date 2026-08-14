import { ATTACKS, FIGHTER } from '../config/gameplay.js';

export class Fighter extends Phaser.GameObjects.Container {
  constructor(scene, { x, y, id, texture, frames = null, tint }) {
    super(scene, x, y);
    this.id = id;
    this.tint = tint;
    this.health = FIGHTER.maxHealth;
    this.facing = id === 'player' ? 1 : -1;
    this.state = 'idle';
    this.cooldowns = {};
    this.lockedUntil = 0;
    this.isInvulnerable = false;
    this.frameTextures = frames ? {
      idle: texture,
      run: (frames.run || []).map((_, index) => `remote-player-run-${index}`),
      jump: 'remote-player-jump',
    } : null;
    scene.add.existing(this);
    scene.physics.add.existing(this);
    this.body.setSize(FIGHTER.bodyWidth, FIGHTER.bodyHeight).setOffset(-FIGHTER.bodyWidth / 2, -FIGHTER.bodyHeight);
    this.body.setCollideWorldBounds(true).setMaxVelocity(600, 900);

    const shadow = scene.add.ellipse(0, -3, 106, 24, 0x7a4b20, .2);
    this.character = scene.add.container(0, 0);
    this.#createBody(scene, tint);
    this.avatar = texture ? scene.add.image(0, -160, texture) : this.#placeholder(scene, tint);
    this.avatar.setDisplaySize(116, 116).setOrigin(.5);
    this.character.add(this.avatar);
    this.#createCollar(scene, tint);
    this.add([shadow, this.character]);

    this.hurtBox = scene.add.rectangle(x, y - 90, FIGHTER.bodyWidth, FIGHTER.bodyHeight, 0x00ff00, 0);
    scene.physics.add.existing(this.hurtBox);
    this.hurtBox.body.setAllowGravity(false);
    this.attackBox = scene.add.rectangle(x, y - 95, 10, 10, 0xff0000, 0);
    scene.physics.add.existing(this.attackBox);
    this.attackBox.body.setAllowGravity(false).enable = false;
  }

  #placeholder(scene, tint) {
    const key = `placeholder-${this.id}`;
    if (!scene.textures.exists(key)) {
      const g = scene.make.graphics({ x: 0, y: 0, add: false });
      g.fillStyle(0xffd7bc).fillCircle(64, 35, 32);
      g.fillStyle(0x171a2e).fillTriangle(27, 36, 48, 0, 59, 34).fillTriangle(52, 25, 82, 0, 96, 39);
      g.fillStyle(0xffffff).fillCircle(52, 34, 7).fillCircle(76, 34, 7);
      g.fillStyle(0x171a2e).fillCircle(53, 35, 3).fillCircle(75, 35, 3);
      g.generateTexture(key, 128, 72); g.destroy();
    }
    return scene.add.image(0, -151, key);
  }

  #createBody(scene, tint) {
    const outline = 0x8c5a2b;
    const trousersBack = 0x9a7346;
    const trousersFront = 0xb48b58;
    const backArm = scene.add.ellipse(-34, -91, 25, 82, tint).setStrokeStyle(2, outline, .7).setOrigin(.5, .12).setAngle(8);
    const backLeg = scene.add.ellipse(-20, -40, 29, 72, trousersBack).setStrokeStyle(2, outline, .65).setOrigin(.5, .1).setAngle(3);
    const frontLeg = scene.add.ellipse(20, -40, 29, 72, trousersFront).setStrokeStyle(2, outline, .65).setOrigin(.5, .1).setAngle(-3);
    const shoulder = scene.add.ellipse(0, -132, 92, 42, tint).setStrokeStyle(2, outline, .6);
    const torso = scene.add.rectangle(0, -94, 82, 76, tint).setStrokeStyle(2, outline, .7);
    const torsoHem = scene.add.ellipse(0, -57, 82, 38, tint).setStrokeStyle(2, outline, .55);
    const belt = scene.add.rectangle(0, -57, 78, 13, 0xffdc82).setStrokeStyle(2, outline, .55);
    const frontArm = scene.add.ellipse(34, -91, 25, 82, Phaser.Display.Color.ValueToColor(tint).brighten(12).color)
      .setStrokeStyle(2, outline, .7)
      .setOrigin(.5, .12).setAngle(-8);
    const leftBoot = scene.add.ellipse(-21, -5, 40, 20, 0x6f4829).setStrokeStyle(2, outline, .6);
    const rightBoot = scene.add.ellipse(21, -5, 40, 20, 0x7f5530).setStrokeStyle(2, outline, .6);
    this.character.add([backArm, backLeg, frontLeg, shoulder, torso, torsoHem, belt, frontArm, leftBoot, rightBoot]);
    this.bodyParts = { backArm, frontArm, backLeg, frontLeg };
  }

  #createCollar(scene, tint) {
    const dark = Phaser.Display.Color.ValueToColor(tint).darken(16).color;
    const collarBase = scene.add.ellipse(0, -119, 70, 27, dark).setStrokeStyle(2, 0x8c5a2b, .55);
    const collarLight = scene.add.ellipse(0, -123, 54, 18, 0xfff0bd).setStrokeStyle(1, 0xb77b36, .45);
    const knot = scene.add.circle(0, -113, 7, 0xffcf63).setStrokeStyle(1, 0x9e682f, .55);
    this.character.add([collarBase, collarLight, knot]);
  }

  update(time, input, opponent) {
    this.facing = opponent.x >= this.x ? 1 : -1;
    this.avatar.setFlipX(this.facing < 0);
    const grounded = this.body.blocked.down;
    if (time >= this.lockedUntil) {
      if (input.attackPressed) this.attack('normal', time);
      else if (input.skill1Pressed) this.attack('dash', time);
      else if (input.skill2Pressed) this.attack('uppercut', time);
      else if (input.skill3Pressed) this.attack('projectile', time);
      else this.#move(input, grounded);
    }
    this.hurtBox.setPosition(this.x, this.y - (input.down && grounded ? 55 : 90));
    this.hurtBox.body.setSize(FIGHTER.bodyWidth, input.down && grounded ? 105 : FIGHTER.bodyHeight);
    if (grounded && time >= this.lockedUntil && !input.axisX) this.body.setVelocityX(0);
    this.#updateVisual(time, grounded);
    this.#animateBody(time, grounded);
  }

  #animateBody(time, grounded) {
    const moving = grounded && (this.state === 'walk' || this.state === 'slide');
    const swing = moving ? Math.sin(time / 105) * 24 : 0;
    this.bodyParts.frontArm.setAngle(-8 + swing);
    this.bodyParts.backArm.setAngle(8 - swing);
    this.bodyParts.frontLeg.setAngle(-3 - swing * .45);
    this.bodyParts.backLeg.setAngle(3 + swing * .45);
    this.character.y = grounded && moving ? Math.abs(Math.sin(time / 105)) * -4 : 0;
    if (!grounded) {
      this.bodyParts.frontArm.setAngle(-45);
      this.bodyParts.backArm.setAngle(45);
      this.bodyParts.frontLeg.setAngle(-18);
      this.bodyParts.backLeg.setAngle(18);
    }
  }

  #updateVisual(time, grounded) {
    if (!this.frameTextures || this.id !== 'player') return;
    let texture = this.frameTextures.idle;
    if (!grounded && this.scene.textures.exists(this.frameTextures.jump)) {
      texture = this.frameTextures.jump;
    } else if (this.state === 'walk' || this.state === 'slide') {
      const run = this.frameTextures.run.filter((key) => this.scene.textures.exists(key));
      if (run.length) texture = run[Math.floor(time / 140) % run.length];
    }
    if (texture && this.scene.textures.exists(texture) && this.avatar.texture.key !== texture) {
      this.avatar.setTexture(texture).setDisplaySize(116, 116);
    }
  }

  #move(input, grounded) {
    if (input.jumpPressed && grounded) {
      const sliding = input.slide && input.axisX;
      this.body.setVelocity(input.axisX * (sliding ? FIGHTER.slideSpeed : FIGHTER.airSpeed), -(sliding ? FIGHTER.slideJumpSpeed : FIGHTER.jumpSpeed));
      this.state = sliding ? 'slideJump' : 'jump';
    } else if (grounded) {
      this.body.setVelocityX(input.axisX * (input.slide ? FIGHTER.slideSpeed : FIGHTER.walkSpeed));
      this.state = input.down ? 'crouch' : input.axisX ? (input.slide ? 'slide' : 'walk') : 'idle';
    } else if (input.axisX) {
      this.body.setVelocityX(Phaser.Math.Linear(this.body.velocity.x, input.axisX * FIGHTER.airSpeed, .08));
    }
  }

  attack(name, time) {
    const config = ATTACKS[name];
    if (!config || time < (this.cooldowns[name] || 0)) return;
    this.cooldowns[name] = time + (config.cooldown || 350);
    this.state = name;
    this.lockedUntil = time + config.startup + config.active + config.recovery;
    this.body.setVelocityX(name === 'dash' ? this.facing * 420 : 0);
    if (name === 'uppercut') this.body.setVelocityY(-520);
    this.scene.time.delayedCall(config.startup, () => {
      if (!this.active) return;
      if (name === 'projectile') return this.scene.combat.spawnProjectile(this);
      this.currentAttack = { name, config, hasHit: false };
      this.attackBox.setPosition(this.x + this.facing * (FIGHTER.bodyWidth / 2 + config.range / 2), this.y - config.height);
      this.attackBox.body.setSize(config.range, config.height).enable = true;
      this.scene.time.delayedCall(config.active, () => { this.attackBox.body.enable = false; this.currentAttack = null; });
    });
  }

  takeHit(attack, direction) {
    this.health = Math.max(0, this.health - attack.damage);
    this.state = 'hit'; this.lockedUntil = this.scene.time.now + 260; this.isInvulnerable = true;
    this.body.setVelocity(direction * attack.knockback, -120);
    this.setAlpha(.55);
    this.scene.time.delayedCall(180, () => { this.isInvulnerable = false; this.setAlpha(1); });
    this.emit('healthChanged', this.health / FIGHTER.maxHealth);
    if (!this.health) this.emit('defeated', this);
  }

  destroy(fromScene) {
    this.hurtBox?.destroy(); this.attackBox?.destroy(); super.destroy(fromScene);
  }
}
