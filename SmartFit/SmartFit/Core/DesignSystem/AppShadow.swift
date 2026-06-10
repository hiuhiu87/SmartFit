import SwiftUI

struct AppShadowStyle {
    let color: Color
    let radius: CGFloat
    let x: CGFloat
    let y: CGFloat
}

enum AppShadow {
    static let none = AppShadowStyle(color: .clear, radius: 0, x: 0, y: 0)
    static let card = AppShadowStyle(color: .black.opacity(0.18), radius: 18, x: 0, y: 10)
    static let elevated = AppShadowStyle(color: .black.opacity(0.28), radius: 28, x: 0, y: 18)
    static let hero = AppShadowStyle(color: AppColors.primary.opacity(0.18), radius: 34, x: 0, y: 20)
}

extension View {
    func appShadow(_ style: AppShadowStyle) -> some View {
        shadow(color: style.color, radius: style.radius, x: style.x, y: style.y)
    }
}
