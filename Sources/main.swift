import AppKit
import Foundation
import SwiftUI

private let petStateURL = URL(fileURLWithPath: "/Users/baijingting/.openclaw/workspace/memory/pet-state.json")
private let petAPIBase = URL(string: "http://127.0.0.1:18793")!
private let learningScript = "/Users/baijingting/.openclaw/scripts/openclaw-learning-intake.sh"
private let screenshotScript = "/Users/baijingting/.openclaw/scripts/openclaw-screenshot-intake.sh"

struct PetState: Codable {
    var name: String
    var species: String
    var emoji: String
    var affinity: Int
    var energy: Int
    var hunger: Int
    var lastAction: String
    var lastUpdated: String
    var rewardStreak: Int
    var level: Int
    var xp: Int
    var totalActions: Int
    var form: String
    var stageID: String
    var stageTitle: String
    var stagePresence: String
    var unlockedFeatures: [String]

    enum CodingKeys: String, CodingKey {
        case name, species, emoji, affinity, energy, hunger, level, xp, form
        case lastAction = "last_action"
        case lastUpdated = "last_updated"
        case rewardStreak = "reward_streak"
        case totalActions = "total_actions"
        case stageID = "stage_id"
        case stageTitle = "stage_title"
        case stagePresence = "stage_presence"
        case unlockedFeatures = "unlocked_features"
    }

    static let fallback = PetState(
        name: "小钳",
        species: "琥珀小龙虾",
        emoji: "🦞",
        affinity: 75,
        energy: 70,
        hunger: 25,
        lastAction: "idle",
        lastUpdated: "",
        rewardStreak: 0,
        level: 1,
        xp: 0,
        totalActions: 0,
        form: "pet",
        stageID: "seed",
        stageTitle: "琥珀幼体",
        stagePresence: "刚学会陪伴，会安静跟着你。",
        unlockedFeatures: ["pet_panel", "pet_actions", "screenshot_send"]
    )
}

@MainActor
final class CompanionStore: ObservableObject {
    @Published var pet: PetState = .fallback
    @Published var hoverActionsVisible = false
    @Published var detailVisible = false
    @Published var learningTopic = ""
    @Published var learningGoal = ""
    @Published var latestStatus = "准备好了，会在一旁陪着你。"
    @Published var latestArtifactPath = ""
    @Published var lastError = ""

    private var timer: Timer?

    init() {
        loadLocalState()
        refreshFromAPI()
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.refreshFromAPI()
            }
        }
    }

    func toggleDetail() {
        detailVisible.toggle()
    }

    func setHover(_ visible: Bool) {
        hoverActionsVisible = visible
    }

    func refreshFromAPI() {
        var request = URLRequest(url: petAPIBase.appendingPathComponent("pet"))
        request.cachePolicy = .reloadIgnoringLocalCacheData
        URLSession.shared.dataTask(with: request) { [weak self] data, _, error in
            Task { @MainActor in
                guard let self else { return }
                if let data, let decoded = try? JSONDecoder().decode(PetState.self, from: data) {
                    self.pet = decoded
                    self.lastError = ""
                    return
                }
                if error != nil {
                    self.loadLocalState()
                }
            }
        }.resume()
    }

    func trigger(action: String) {
        var request = URLRequest(url: petAPIBase.appendingPathComponent("pet/action"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["action": action])
        URLSession.shared.dataTask(with: request) { [weak self] data, _, _ in
            Task { @MainActor in
                guard let self else { return }
                if let data,
                   let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let petJSON = payload["pet"],
                   let petData = try? JSONSerialization.data(withJSONObject: petJSON),
                   let decoded = try? JSONDecoder().decode(PetState.self, from: petData) {
                    self.pet = decoded
                    self.latestStatus = self.statusText(for: action)
                } else {
                    self.latestStatus = "动作没接上，但我还在。"
                }
            }
        }.resume()
    }

    func queueLearning() {
        let topic = learningTopic.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !topic.isEmpty else {
            lastError = "先输入想学习的内容。"
            return
        }
        let goal = learningGoal.trimmingCharacters(in: .whitespacesAndNewlines)
        runProcess(launchPath: learningScript, arguments: [topic, goal]) { [weak self] output in
            guard let self else { return }
            self.latestStatus = "学习请求已经入队，小钳会继续盯着这条线。"
            self.latestArtifactPath = output
            self.lastError = ""
            self.learningTopic = ""
            self.learningGoal = ""
        } onError: { [weak self] message in
            self?.lastError = message
        }
    }

    func captureAndQueue() {
        let topic = learningTopic.trimmingCharacters(in: .whitespacesAndNewlines)
        let goal = learningGoal.trimmingCharacters(in: .whitespacesAndNewlines)
        runProcess(launchPath: screenshotScript, arguments: [topic, goal]) { [weak self] output in
            guard let self else { return }
            self.latestStatus = "截图和说明已经打包进 OpenClaw 执行流。"
            self.latestArtifactPath = output
            self.lastError = ""
        } onError: { [weak self] message in
            self?.lastError = message
        }
    }

    private func loadLocalState() {
        if let data = try? Data(contentsOf: petStateURL),
           let decoded = try? JSONDecoder().decode(PetState.self, from: data) {
            pet = decoded
        }
    }

    private func runProcess(launchPath: String, arguments: [String], onSuccess: @escaping (String) -> Void, onError: @escaping (String) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: launchPath)
            process.arguments = arguments

            let outputPipe = Pipe()
            let errorPipe = Pipe()
            process.standardOutput = outputPipe
            process.standardError = errorPipe

            do {
                try process.run()
                process.waitUntilExit()
                let output = String(data: outputPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                let error = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                DispatchQueue.main.async {
                    if process.terminationStatus == 0 {
                        onSuccess(output.trimmingCharacters(in: .whitespacesAndNewlines))
                    } else {
                        onError(error.isEmpty ? "执行失败" : error)
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    onError(error.localizedDescription)
                }
            }
        }
    }

    private func statusText(for action: String) -> String {
        switch action {
        case "feed": return "被投喂到了，现在心情软了一点。"
        case "play": return "刚陪它玩了一下，活力明显上来了。"
        case "nap": return "它眯了一会，现在又精神了。"
        default: return "动作完成。"
        }
    }
}

final class FloatingPanel: NSPanel {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var panel: FloatingPanel?
    private let store = CompanionStore()

    func applicationDidFinishLaunching(_ notification: Notification) {
        let contentView = CompanionRootView(store: store)
        let hosting = NSHostingView(rootView: contentView)

        let panel = FloatingPanel(
            contentRect: NSRect(x: 0, y: 0, width: 360, height: 640),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.isFloatingPanel = true
        panel.level = .statusBar
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        panel.backgroundColor = .clear
        panel.isOpaque = false
        panel.hasShadow = false
        panel.hidesOnDeactivate = false
        panel.isMovableByWindowBackground = true
        panel.contentView = hosting
        panel.setFrameOrigin(NSPoint(x: NSScreen.main!.visibleFrame.maxX - 390, y: NSScreen.main!.visibleFrame.midY - 180))
        panel.orderFrontRegardless()
        self.panel = panel
    }
}

struct CompanionRootView: View {
    @ObservedObject var store: CompanionStore
    @State private var hovering = false

    var body: some View {
        ZStack(alignment: .topTrailing) {
            if store.detailVisible {
                detailPanel
                    .transition(.move(edge: .trailing).combined(with: .opacity))
            }
            floatingCore
        }
        .frame(width: store.detailVisible ? 360 : 220, height: store.detailVisible ? 640 : 120, alignment: .topTrailing)
        .padding(12)
        .animation(.spring(response: 0.28, dampingFraction: 0.88), value: store.detailVisible)
        .onHover { inside in
            hovering = inside
            store.setHover(inside)
        }
    }

    private var floatingCore: some View {
        HStack(spacing: 10) {
            avatar
            if store.hoverActionsVisible || store.detailVisible {
                quickActions
                    .transition(.opacity.combined(with: .move(edge: .trailing)))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().stroke(Color.white.opacity(0.65), lineWidth: 1))
        .shadow(color: .black.opacity(0.14), radius: 18, y: 10)
    }

    private var avatar: some View {
        Button {
            store.toggleDetail()
        } label: {
            HStack(spacing: 10) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(colors: [Color(red: 1.0, green: 0.92, blue: 0.86), Color(red: 1.0, green: 0.74, blue: 0.60)],
                                           startPoint: .topLeading,
                                           endPoint: .bottomTrailing)
                        )
                        .frame(width: 46, height: 46)
                    Circle()
                        .stroke(Color(red: 1.0, green: 0.73, blue: 0.58).opacity(0.45), lineWidth: 6)
                        .frame(width: 56, height: 56)
                    VStack(spacing: 2) {
                        HStack(spacing: 7) {
                            Circle().fill(Color(red: 0.17, green: 0.23, blue: 0.36)).frame(width: 5, height: 5)
                            Circle().fill(Color(red: 0.17, green: 0.23, blue: 0.36)).frame(width: 5, height: 5)
                        }
                        Capsule().fill(Color(red: 0.72, green: 0.43, blue: 0.33)).frame(width: 14, height: 3)
                    }
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text(store.pet.name)
                        .font(.system(size: 15, weight: .semibold))
                    Text("Lv.\(store.pet.level) · \(store.pet.stageTitle)")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
            }
        }
        .buttonStyle(.plain)
    }

    private var quickActions: some View {
        HStack(spacing: 8) {
            quickButton("喂", color: Color.orange.opacity(0.18)) { store.trigger(action: "feed") }
            quickButton("玩", color: Color.blue.opacity(0.18)) { store.trigger(action: "play") }
            quickButton("睡", color: Color.purple.opacity(0.18)) { store.trigger(action: "nap") }
            quickButton("学", color: Color.green.opacity(0.18)) { store.detailVisible = true }
            quickButton("截", color: Color.black.opacity(0.12)) { store.captureAndQueue() }
        }
    }

    private func quickButton(_ title: String, color: Color, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .frame(width: 34, height: 34)
                .background(color, in: Circle())
        }
        .buttonStyle(.plain)
    }

    private var detailPanel: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(store.pet.emoji) \(store.pet.name)")
                            .font(.system(size: 17, weight: .bold))
                        Text(store.pet.species)
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text("Lv.\(store.pet.level)")
                        .font(.system(size: 12, weight: .semibold))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(Color.blue.opacity(0.08), in: Capsule())
                }

                companionCard
                statCard
                evolutionCard
                learningCard
                statusCard
            }
            .padding(16)
        }
        .frame(width: 360, height: 640)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 28, style: .continuous).stroke(Color.white.opacity(0.7), lineWidth: 1))
        .shadow(color: .black.opacity(0.18), radius: 24, y: 12)
    }

    private var companionCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(store.pet.stagePresence)
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(Color(red: 0.19, green: 0.27, blue: 0.40))
            Text(store.latestStatus)
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(colors: [Color(red: 1.0, green: 0.96, blue: 0.92), Color(red: 0.94, green: 0.96, blue: 1.0)],
                           startPoint: .topLeading,
                           endPoint: .bottomTrailing),
            in: RoundedRectangle(cornerRadius: 20, style: .continuous)
        )
    }

    private var statCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            StatRow(title: "亲密度", value: store.pet.affinity)
            StatRow(title: "精力值", value: store.pet.energy)
            StatRow(title: "饥饿值", value: store.pet.hunger)
        }
        .padding(14)
        .background(Color.white.opacity(0.72), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    private var evolutionCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("进化进度")
                    .font(.system(size: 13, weight: .semibold))
                Spacer()
                Text("XP \(store.pet.xp)/100")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
            }
            ProgressView(value: Double(store.pet.xp), total: 100)
                .tint(.orange)
            Text("当前阶段：\(store.pet.stageTitle)")
                .font(.system(size: 12, weight: .medium))
            Text("累计互动：\(store.pet.totalActions) 次")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .background(Color.orange.opacity(0.10), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    private var learningCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("外部学习")
                .font(.system(size: 13, weight: .semibold))
            TextField("想让它持续学习什么，例如：Chrome 扩展开发、Notion 自动化", text: $store.learningTopic)
                .textFieldStyle(.roundedBorder)
            TextField("学习目标，可选。例如：整理成可落地方案和 skill 草稿", text: $store.learningGoal)
                .textFieldStyle(.roundedBorder)
            HStack(spacing: 8) {
                Button("入队学习") { store.queueLearning() }
                    .buttonStyle(.borderedProminent)
                Button("全局截屏入队") { store.captureAndQueue() }
                    .buttonStyle(.bordered)
            }
            Text("这条学习请求会进入 OpenClaw 的学习流，先形成方案和经验沉淀，再长成 skill 草稿。")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .background(Color.green.opacity(0.10), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("最近结果")
                .font(.system(size: 13, weight: .semibold))
            if !store.latestArtifactPath.isEmpty {
                Text(store.latestArtifactPath)
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                    .textSelection(.enabled)
            }
            if !store.lastError.isEmpty {
                Text(store.lastError)
                    .font(.system(size: 11))
                    .foregroundStyle(.red)
            }
            Text("上次同步：\(store.pet.lastUpdated.isEmpty ? "刚刚" : store.pet.lastUpdated)")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .background(Color.blue.opacity(0.08), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }
}

struct StatRow: View {
    let title: String
    let value: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title).font(.system(size: 12))
                Spacer()
                Text("\(value)").font(.system(size: 12, weight: .semibold))
            }
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.black.opacity(0.08))
                    Capsule()
                        .fill(
                            LinearGradient(colors: [Color.orange, Color.yellow, Color.blue.opacity(0.65)],
                                           startPoint: .leading,
                                           endPoint: .trailing)
                        )
                        .frame(width: geometry.size.width * CGFloat(value) / 100)
                }
            }
            .frame(height: 8)
        }
    }
}

@main
struct LittleClawCompanionApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}
