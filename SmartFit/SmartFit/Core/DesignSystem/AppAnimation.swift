import SwiftUI

enum AppAnimation {
    static let quick = Animation.easeOut(duration: 0.16)
    static let standard = Animation.spring(response: 0.32, dampingFraction: 0.86)
    static let emphasized = Animation.spring(response: 0.48, dampingFraction: 0.82)
}
