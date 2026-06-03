import Foundation

struct APIErrorEnvelope: Decodable {
    let code: String
    let message: String
}

struct APIResponseEnvelope<T: Decodable>: Decodable {
    let success: Bool
    let code: String?
    let message: String?
    let data: T?
    let error: APIErrorEnvelope?
    let requestID: String?
    let serverTime: String?

    enum CodingKeys: String, CodingKey {
        case success
        case code
        case message
        case data
        case error
        case requestID = "request_id"
        case serverTime = "server_time"
    }
}
