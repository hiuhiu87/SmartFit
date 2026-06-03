import Foundation

final class OnboardingRepository {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func updateProfile(_ payload: ProfileUpdateRequest) async throws -> UserProfile {
        try await apiClient.put(
            APIEndpoint(path: "/api/v1/users/me/profile", method: .put),
            body: payload,
            as: UserProfile.self
        )
    }

    func updateEquipment(_ payload: EquipmentUpdateRequest) async throws -> [String] {
        let response = try await apiClient.put(
            APIEndpoint(path: "/api/v1/users/me/equipment", method: .put),
            body: payload,
            as: EquipmentUpdateResponse.self
        )
        return response.equipmentTypes
    }

    func fetchCurrentUser() async throws -> CurrentUserResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/users/me", method: .get),
            as: CurrentUserResponse.self
        )
    }
}

private struct EquipmentUpdateResponse: Codable {
    let equipmentTypes: [String]

    enum CodingKeys: String, CodingKey {
        case equipmentTypes = "equipment_types"
    }
}
