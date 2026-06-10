import SwiftUI

enum AppTypography {
    static let largeTitle = Font.system(size: 34, weight: .bold, design: .rounded)
    static let hero = largeTitle
    static let title = Font.system(size: 22, weight: .semibold, design: .rounded)
    static let headline = Font.system(size: 17, weight: .semibold, design: .rounded)
    static let body = Font.system(size: 16, weight: .regular, design: .default)
    static let caption = Font.system(size: 13, weight: .medium, design: .default)
    static let metric = Font.system(size: 28, weight: .bold, design: .rounded)
    static let metricNumber = Font.system(size: 44, weight: .bold, design: .rounded)
}
