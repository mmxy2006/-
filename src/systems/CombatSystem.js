import { ATTACKS } from '../config/gameplay.js';

export class CombatSystem {
  constructor(scene) {
    this.scene = scene;
    this.projectiles = scene.physics.add.group();
  }

  bind(a, b) {
    this.scene.physics.add.overlap(a.attackBox, b.hurtBox, () => this.#resolveMelee(a, b));
    this.scene.physics.add.overlap(b.attackBox, a.hurtBox, () => this.#resolveMelee(b, a));
    this.scene.physics.add.overlap(this.projectiles, a.hurtBox, (one, two) => this.#resolveProjectile(one.attack ? one : two, a));
    this.scene.physics.add.overlap(this.projectiles, b.hurtBox, (one, two) => this.#resolveProjectile(one.attack ? one : two, b));
  }

  spawnProjectile(owner) {
    const direction = owner.facing;
    const orb = this.scene.add.circle(owner.x + direction * 70, owner.y - 105, 23, owner.tint, 1);
    this.scene.physics.add.existing(orb);
    this.projectiles.add(orb);
    orb.owner = owner;
    orb.attack = ATTACKS.projectile;
    orb.body.setAllowGravity(false).setVelocityX(direction * 560);
    this.scene.tweens.add({ targets: orb, scale: 1.25, alpha: .65, yoyo: true, repeat: -1, duration: 160 });
    this.scene.time.delayedCall(2600, () => orb.active && orb.destroy());
  }

  #resolveMelee(attacker, defender) {
    if (!attacker.currentAttack || attacker.currentAttack.hasHit || defender.isInvulnerable) return;
    attacker.currentAttack.hasHit = true;
    defender.takeHit(attacker.currentAttack.config, attacker.facing);
    this.scene.events.emit('combat:hit', { attacker, defender });
  }

  #resolveProjectile(projectile, defender) {
    if (!projectile?.active || !projectile.attack || projectile.owner === defender || defender.isInvulnerable) return;
    defender.takeHit(projectile.attack, Math.sign(projectile.body.velocity.x));
    projectile.destroy();
    this.scene.events.emit('combat:hit', { attacker: projectile.owner, defender });
  }
}
