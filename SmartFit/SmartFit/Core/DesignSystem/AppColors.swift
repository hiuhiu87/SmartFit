import SwiftUI

// Dark-first color tokens. New UI should consume these tokens instead of hard-coded colors
// so future features inherit the app theme consistently.
enum AppColors {
    static let primary = Color(red: 0.20, green: 0.86, blue: 0.72)
    static let secondary = Color(red: 0.99, green: 0.72, blue: 0.28)
    static let background = Color(red: 0.04, green: 0.06, blue: 0.08)
    static let backgroundSecondary = Color(red: 0.07, green: 0.09, blue: 0.13)
    static let surface = Color(red: 0.09, green: 0.12, blue: 0.16)
    static let surfaceElevated = Color(red: 0.13, green: 0.17, blue: 0.22)
    static let surfaceMuted = Color(red: 0.17, green: 0.21, blue: 0.27)
    static let border = Color.white.opacity(0.10)
    static let textPrimary = Color(red: 0.96, green: 0.98, blue: 1.00)
    static let textSecondary = Color(red: 0.64, green: 0.70, blue: 0.77)
    static let textInverse = Color(red: 0.05, green: 0.07, blue: 0.10)
    static let danger = Color(red: 1.00, green: 0.42, blue: 0.42)
    static let error = danger
    static let success = Color(red: 0.33, green: 0.86, blue: 0.55)
    static let warning = Color(red: 0.98, green: 0.72, blue: 0.26)
}
