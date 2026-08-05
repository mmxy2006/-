export class PveController {
  constructor(fighter, target) {
    this.fighter = fighter;
    this.target = target;
    this.nextDecisionAt = 0;
    this.intent = {};
  }

  update(time) {
    if (time >= this.nextDecisionAt) {
      const distance = Math.abs(this.target.x - this.fighter.x);
      const toward = Math.sign(this.target.x - this.fighter.x);
      this.intent = { axisX: distance > 125 ? toward : distance < 78 ? -toward : 0 };
      const roll = Math.random();
      if (distance < 150 && roll < .48) this.intent.attackPressed = true;
      else if (distance < 230 && roll < .68) this.intent.skill1Pressed = true;
      else if (distance > 300 && roll < .82) this.intent.skill3Pressed = true;
      else if (roll > .92) this.intent.jumpPressed = true;
      this.nextDecisionAt = time + Phaser.Math.Between(220, 520);
    }
    const frame = { ...this.intent };
    this.intent.attackPressed = this.intent.skill1Pressed = this.intent.skill3Pressed = this.intent.jumpPressed = false;
    return frame;
  }
}
