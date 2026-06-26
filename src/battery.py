class Battery:
    def __init__(self, charge: float = 100.0):
        self.charge = charge
        self.warning_active = False

    def drain(self, amount: float):
        self.charge = max(0.0, self.charge - amount)
        if self.charge < 20.0:
            self.warning_active = True

    def recharge(self, amount: float):
        self.charge = min(100.0, self.charge + amount)
        if self.charge >= 20.0:
            self.warning_active = False
