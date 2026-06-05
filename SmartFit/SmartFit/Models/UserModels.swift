import Foundation

struct UserProfile: Codable {
    let fullName: String?
    let age: Int?
    let heightCM: Double?
    let weightKG: Double?
    let trainingLevel: String?
    let primaryGoal: String?
    let injuries: [String]
    let notes: String?
    let trainingStyle: String?

    enum CodingKeys: String, CodingKey {
        case fullName = "full_name"
        case age
        case heightCM = "height_cm"
        case weightKG = "weight_kg"
        case trainingLevel = "training_level"
        case primaryGoal = "primary_goal"
        case injuries
        case notes
        case trainingStyle = "training_style"
    }
}

struct UserEquipment: Codable, Identifiable, Hashable {
    let equipmentType: String
    var id: String { equipmentType }

    enum CodingKeys: String, CodingKey {
        case equipmentType = "equipment_type"
    }
}

struct CurrentUserResponse: Codable {
    let id: UUID
    let email: String
    let isActive: Bool
    let profile: UserProfile?
    let equipmentTypes: [String]

    enum CodingKeys: String, CodingKey {
        case id = "user_id"
        case email
        case isActive = "is_active"
        case profile
        case equipmentTypes = "equipment_types"
    }

    var isOnboardingComplete: Bool {
        profile != nil && !equipmentTypes.isEmpty
    }
}

struct ProfileUpdateRequest: Codable {
    let fullName: String?
    let age: Int?
    let heightCM: Double?
    let weightKG: Double?
    let trainingLevel: String
    let primaryGoal: String
    let injuries: [String]
    let notes: String?
    let trainingStyle: String?

    enum CodingKeys: String, CodingKey {
        case fullName = "full_name"
        case age
        case heightCM = "height_cm"
        case weightKG = "weight_kg"
        case trainingLevel = "training_level"
        case primaryGoal = "primary_goal"
        case injuries
        case notes
        case trainingStyle = "training_style"
    }
}

struct EquipmentUpdateRequest: Codable {
    let equipmentTypes: [String]

    enum CodingKeys: String, CodingKey {
        case equipmentTypes = "equipment_types"
    }
}
