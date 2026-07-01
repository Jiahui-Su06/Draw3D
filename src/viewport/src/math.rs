#[derive(Clone, Copy, Debug)]
pub(crate) struct Vec3 {
    pub(crate) x: f32,
    pub(crate) y: f32,
    pub(crate) z: f32,
}

impl Vec3 {
    pub(crate) fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
    }

    pub(crate) fn dot(self, rhs: Self) -> f32 {
        self.x * rhs.x + self.y * rhs.y + self.z * rhs.z
    }

    pub(crate) fn length(self) -> f32 {
        self.dot(self).sqrt()
    }

    pub(crate) fn normalized(self) -> Self {
        let length = self.length();
        if length <= f32::EPSILON {
            return Self::new(1.0, 0.0, 0.0);
        }
        self * (1.0 / length)
    }

    pub(crate) fn to_array(self) -> [f32; 3] {
        [self.x, self.y, self.z]
    }

    pub(crate) fn to_vec4(self, w: f32) -> [f32; 4] {
        [self.x, self.y, self.z, w]
    }
}

impl std::ops::Add for Vec3 {
    type Output = Self;

    fn add(self, rhs: Self) -> Self::Output {
        Self::new(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)
    }
}

impl std::ops::Sub for Vec3 {
    type Output = Self;

    fn sub(self, rhs: Self) -> Self::Output {
        Self::new(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)
    }
}

impl std::ops::Mul<f32> for Vec3 {
    type Output = Self;

    fn mul(self, rhs: f32) -> Self::Output {
        Self::new(self.x * rhs, self.y * rhs, self.z * rhs)
    }
}
