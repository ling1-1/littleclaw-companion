(function () {
  'use strict';

  const MAIN_SIZE = { width: 176, height: 196 };
  const COMPACT_SIZE = { width: 58, height: 58 };

  const BUBBLE_LINES = {
    idle: ['我在这儿陪你。', '继续推进吧，我盯着。', '今天也一起做完。'],
    feed: ['好香，状态回来了。', '补给完成，可以继续。', '这口吃下去舒服了。'],
    play: ['我精神起来了。', '继续，配合更顺了。', '玩一下脑子都转快了。'],
    sleep: ['我先眯一下。', '恢复中，马上回来。', '让我缓一会儿。'],
    talk: ['我去替你递话。', '收到，我已经在传。', '这句我帮你送过去。'],
    think: ['我在整理思路。', '等我把线头收一收。', '先让我想清楚。'],
    happy: ['嘿，我喜欢这样。', '这样很好，再来一点。', '我接住你了。'],
    alert: ['有新动静。', '我看见变化了。', '这一步有反馈。'],
  };

  const ROLE_VOICE = {
    guardian: { idle: ['我先替你守着。', '节奏先稳住。'], think: ['我先兜住这条线。'], alert: ['这里我来盯着。'] },
    runner: { idle: ['下一步可以继续推。', '我准备往前拱。'], think: ['我在找推进口。'], alert: ['可以继续压一步。'] },
    captain: { idle: ['我帮你看节奏。', '先盯住全局。'], think: ['我在排下一步顺序。'], alert: ['这条线该收一下了。'] },
    watcher: { idle: ['我先看细节。', '这里我帮你观察。'], think: ['我在找异常点。'], alert: ['我看到变化了。'] },
    guide: { idle: ['我帮你理一下方向。', '先把线头理顺。'], think: ['我在串思路。'], alert: ['方向有了。'] },
    oracle: { idle: ['我先听一听风向。', '让我感一下这条线。'], think: ['我在收束判断。'], alert: ['这一步有答案感。'] },
    repair: { idle: ['我先看故障点。', '这块我来排查。'], think: ['我在找根因。'], alert: ['这里需要修一下。'] },
    builder: { idle: ['我先搭结构。', '这条线可以开工。'], think: ['我在拼实现路径。'], alert: ['可以开始落了。'] },
    warden: { idle: ['我先稳住运行。', '我在看护这条链。'], think: ['我在查风险。'], alert: ['状态有波动。'] },
    lullaby: { idle: ['慢一点也没关系。', '我会安静陪着。'], think: ['我在替你慢慢整理。'], alert: ['这一步我记住了。'] },
    scribe: { idle: ['我先记下来。', '这条线我来沉淀。'], think: ['我在收成笔记。'], alert: ['这一点值得记。'] },
    lantern: { idle: ['我会给你留着灯。', '夜里也别急。'], think: ['我在替你守着这条线。'], alert: ['这里亮了一下。'] },
    keeper: { idle: ['先放我这里。', '我帮你兜一下。'], think: ['我在收拢这些碎片。'], alert: ['这条我接住了。'] },
    healer: { idle: ['先缓一口气。', '我陪你慢慢来。'], think: ['我在帮你降噪。'], alert: ['这一步先别着急。'] },
    porter: { idle: ['我来帮你搬运。', '这条线我先接续上。'], think: ['我在找衔接点。'], alert: ['可以往下接了。'] },
    scout: { idle: ['我先去探路。', '我帮你看看前面。'], think: ['我在巡这条线。'], alert: ['我带回消息了。'] },
    messenger: { idle: ['我适合来回传话。', '我随时可以递送。'], think: ['我在找最快路径。'], alert: ['我先替你送过去。'] },
    captain: { idle: ['我先帮你领航。', '下一步我盯着。'], think: ['我在看航线。'], alert: ['方向已经清了。'] },
  };

  const SPECIES = {
    lobster: {
      seed: {
        title: '琥珀幼体',
        palette: { body: '#e98757', shell: '#c65433', belly: '#ffd3b3', line: '#8a3d24', accent: '#ffbf8a', aura: 'rgba(255,171,112,.24)' },
        body: { rx: 34, ry: 30, shellRy: 16, eyeGlow: false, claws: 44, legs: 3, crest: 0, tail: 10, spikes: 0, whisker: 16, fins: 0, whiskerBulbs: 1, ring: 0 },
      },
      coral: {
        title: '珊瑚巡游虾',
        palette: { body: '#ff8b74', shell: '#d8645a', belly: '#ffe0d2', line: '#b24c45', accent: '#ffcfb4', aura: 'rgba(255,154,132,.24)' },
        body: { rx: 36, ry: 31, shellRy: 17, eyeGlow: false, claws: 48, legs: 3, crest: 6, tail: 12, spikes: 1, whisker: 19, fins: 2, whiskerBulbs: 2, ring: 0 },
      },
      reef: {
        title: '礁岩战虾',
        palette: { body: '#df664d', shell: '#a52f2b', belly: '#ffd7cc', line: '#79211d', accent: '#ffb29d', aura: 'rgba(228,95,81,.26)' },
        body: { rx: 38, ry: 32, shellRy: 18, eyeGlow: true, claws: 51, legs: 4, crest: 10, tail: 14, spikes: 3, whisker: 22, fins: 3, whiskerBulbs: 2, ring: 0 },
      },
      royal: {
        title: '王冠龙虾',
        palette: { body: '#f0674a', shell: '#cf4535', belly: '#ffe9d8', line: '#7a221a', accent: '#ffd070', aura: 'rgba(255,176,102,.32)' },
        body: { rx: 39, ry: 33, shellRy: 19, eyeGlow: true, claws: 53, legs: 4, crest: 15, tail: 15, spikes: 4, whisker: 24, fins: 4, whiskerBulbs: 3, ring: 1 },
      },
      mythic: {
        title: '赤曜龙王',
        palette: { body: '#d6493c', shell: '#b72e28', belly: '#fff0e4', line: '#6b1712', accent: '#ffbd57', aura: 'rgba(255,104,72,.36)' },
        body: { rx: 41, ry: 34, shellRy: 20, eyeGlow: true, claws: 56, legs: 4, crest: 19, tail: 16, spikes: 5, whisker: 27, fins: 5, whiskerBulbs: 3, ring: 2 },
      },
    },
    sprite: {
      seed: {
        title: '微光幼灵',
        palette: { body: '#cdb9ff', shell: '#f4eeff', belly: '#ffffff', line: '#7258b8', accent: '#fff5c7', aura: 'rgba(190,173,255,.28)' },
        body: { rx: 28, ry: 35, wings: 1, halo: 12, tail: 12, crown: 0, fringe: 1, shards: 2, orbitals: 0, gown: 0, antenna: 0 },
      },
      mist: {
        title: '流雾信使',
        palette: { body: '#b7dbff', shell: '#eff8ff', belly: '#ffffff', line: '#4c79b5', accent: '#dff6ff', aura: 'rgba(158,207,255,.28)' },
        body: { rx: 29, ry: 37, wings: 2, halo: 16, tail: 14, crown: 0, fringe: 2, shards: 3, orbitals: 1, gown: 1, antenna: 1 },
      },
      star: {
        title: '星羽使灵',
        palette: { body: '#ffd1eb', shell: '#fff4fb', belly: '#ffffff', line: '#a2508c', accent: '#fff3a3', aura: 'rgba(255,196,228,.3)' },
        body: { rx: 31, ry: 38, wings: 3, halo: 18, tail: 16, crown: 3, fringe: 3, shards: 4, orbitals: 2, gown: 2, antenna: 2 },
      },
      oracle: {
        title: '曜纹灵使',
        palette: { body: '#c9b6ff', shell: '#faf6ff', belly: '#ffffff', line: '#6c53b7', accent: '#ffe29c', aura: 'rgba(206,180,255,.34)' },
        body: { rx: 32, ry: 40, wings: 4, halo: 22, tail: 20, crown: 6, fringe: 4, shards: 5, orbitals: 3, gown: 3, antenna: 2 },
      },
    },
    mecha: {
      seed: {
        title: '原型机',
        palette: { body: '#94a7bb', shell: '#cfd9e2', belly: '#eef4f8', line: '#47596a', accent: '#78d4ff', aura: 'rgba(141,187,221,.24)' },
        body: { rx: 28, ry: 29, horns: 0, arms: 29, fins: 0, core: 9, plates: 1, boosters: 0, shoulders: 0, legs: 0, visor: 0, ring: 0, crest: 0 },
      },
      servo: {
        title: '伺服助手',
        palette: { body: '#7f95a9', shell: '#dce7ef', belly: '#f4f8fb', line: '#394c5d', accent: '#80e8ff', aura: 'rgba(123,175,221,.24)' },
        body: { rx: 30, ry: 31, horns: 1, arms: 32, fins: 1, core: 11, plates: 2, boosters: 0, shoulders: 1, legs: 1, visor: 0, ring: 0, crest: 1 },
      },
      forge: {
        title: '锻炉机宠',
        palette: { body: '#8e7d69', shell: '#d3c4b4', belly: '#f4e8dd', line: '#4f4035', accent: '#ffb56b', aura: 'rgba(217,145,88,.28)' },
        body: { rx: 34, ry: 31, horns: 2, arms: 36, fins: 2, core: 12, plates: 4, boosters: 1, shoulders: 2, legs: 2, visor: 1, ring: 0, crest: 2 },
      },
      core: {
        title: '钛心智核',
        palette: { body: '#73839a', shell: '#dce4f5', belly: '#f8fbff', line: '#2d3847', accent: '#73f2ff', aura: 'rgba(130,207,255,.32)' },
        body: { rx: 35, ry: 30, horns: 2, arms: 39, fins: 3, core: 14, plates: 5, boosters: 2, shoulders: 3, legs: 3, visor: 1, ring: 1, crest: 3 },
      },
    },
    moth: {
      seed: {
        title: '茸灯幼蛾',
        palette: { body: '#e5d3c1', shell: '#fff4eb', belly: '#fffdf8', line: '#725850', accent: '#ffe39a', aura: 'rgba(255,226,155,.24)' },
        body: { rx: 24, ry: 32, wings: 1, wingSpan: 28, antenna: 1, fluff: 1, tail: 10, crescent: 0, dust: 2, crown: 0 },
      },
      veil: {
        title: '纱翼夜蛾',
        palette: { body: '#c7b8d6', shell: '#faf5ff', belly: '#fffafc', line: '#665279', accent: '#ffe6aa', aura: 'rgba(210,193,255,.28)' },
        body: { rx: 26, ry: 34, wings: 2, wingSpan: 32, antenna: 2, fluff: 2, tail: 12, crescent: 1, dust: 3, crown: 0 },
      },
      luna: {
        title: '月纹眠蛾',
        palette: { body: '#b2c0df', shell: '#f5f8ff', belly: '#ffffff', line: '#50607e', accent: '#fff3ba', aura: 'rgba(175,203,255,.3)' },
        body: { rx: 27, ry: 36, wings: 3, wingSpan: 35, antenna: 2, fluff: 3, tail: 14, crescent: 2, dust: 4, crown: 1 },
      },
      eclipse: {
        title: '蚀光守夜蛾',
        palette: { body: '#8d88b8', shell: '#f7f2ff', belly: '#ffffff', line: '#48416d', accent: '#ffe08c', aura: 'rgba(181,169,255,.34)' },
        body: { rx: 29, ry: 37, wings: 4, wingSpan: 38, antenna: 2, fluff: 4, tail: 16, crescent: 3, dust: 5, crown: 2 },
      },
    },
    slime: {
      seed: {
        title: '软糖幼体',
        palette: { body: '#91e5c9', shell: '#d7fff0', belly: '#f7fff9', line: '#3d7d6f', accent: '#9df6d3', aura: 'rgba(156,245,211,.24)' },
        body: { rx: 28, ry: 26, wobble: 4, buds: 0, droplets: 1, halo: 0, sparkles: 1, core: 7 },
      },
      puff: {
        title: '泡泡胶灵',
        palette: { body: '#91d4ff', shell: '#e9f9ff', belly: '#f7ffff', line: '#457499', accent: '#cbf6ff', aura: 'rgba(145,212,255,.24)' },
        body: { rx: 31, ry: 28, wobble: 5, buds: 1, droplets: 2, halo: 1, sparkles: 2, core: 8 },
      },
      mellow: {
        title: '绵云凝胶',
        palette: { body: '#d2b8ff', shell: '#f8f2ff', belly: '#ffffff', line: '#6d55a1', accent: '#ffdff6', aura: 'rgba(210,184,255,.28)' },
        body: { rx: 33, ry: 30, wobble: 6, buds: 2, droplets: 3, halo: 1, sparkles: 3, core: 9 },
      },
      nova: {
        title: '星核史莱姆',
        palette: { body: '#ffb9d7', shell: '#fff1f7', belly: '#ffffff', line: '#9e5575', accent: '#fff2b6', aura: 'rgba(255,185,215,.32)' },
        body: { rx: 35, ry: 32, wobble: 7, buds: 3, droplets: 4, halo: 2, sparkles: 4, core: 10 },
      },
    },
    avian: {
      seed: {
        title: '啾羽雏鸟',
        palette: { body: '#f8bd8b', shell: '#fff2e5', belly: '#fffaf5', line: '#86543c', accent: '#ffd85a', aura: 'rgba(255,207,148,.26)' },
        body: { rx: 24, ry: 28, wingLift: 1, crest: 0, tail: 2, orbit: 0, plume: 1, beak: 8 },
      },
      glide: {
        title: '巡风信鸟',
        palette: { body: '#96c9ff', shell: '#eef7ff', belly: '#ffffff', line: '#456b96', accent: '#c6ecff', aura: 'rgba(150,201,255,.26)' },
        body: { rx: 26, ry: 30, wingLift: 2, crest: 1, tail: 3, orbit: 1, plume: 2, beak: 9 },
      },
      crest: {
        title: '冠羽哨鸟',
        palette: { body: '#9dd3b1', shell: '#f1fff6', belly: '#ffffff', line: '#48705b', accent: '#fff0a8', aura: 'rgba(157,211,177,.28)' },
        body: { rx: 28, ry: 31, wingLift: 3, crest: 2, tail: 4, orbit: 1, plume: 3, beak: 10 },
      },
      sky: {
        title: '苍穹领航鸟',
        palette: { body: '#7fa5ff', shell: '#f1f5ff', belly: '#ffffff', line: '#3e5698', accent: '#fff1a0', aura: 'rgba(127,165,255,.34)' },
        body: { rx: 29, ry: 33, wingLift: 4, crest: 3, tail: 5, orbit: 2, plume: 4, beak: 11 },
      },
    },
  };

  const S = {
    tick: 0,
    species: 'lobster',
    stage: 'seed',
    rarity: 'common',
    petName: '伙伴',
    roleId: 'companion',
    roleTitle: '陪伴型',
    mood: 'idle',
    moodTimer: 0,
    speech: '我在这儿陪你。',
    speechTimer: 0,
    blink: 0,
    eyeX: 0,
    eyeY: 0,
    pointerX: 0,
    pointerY: 0,
    particles: [],
    glowPulse: 0,
    lastAction: '',
    lastLevel: 1,
    lastStage: 'seed',
    pending: false,
    running: false,
  };

  let mainCanvas = null;
  let compactCanvas = null;
  let mainCtx = null;
  let compactCtx = null;
  let bubbleMain = null;
  let bubbleCompact = null;

  function stageSpec(species, stage) {
    const family = SPECIES[species] || SPECIES.lobster;
    return family[stage] || family.seed;
  }

  function pickBubble(mood) {
    const roleLines = (ROLE_VOICE[S.roleId] && ROLE_VOICE[S.roleId][mood]) || null;
    const lines = roleLines || BUBBLE_LINES[mood] || BUBBLE_LINES.idle;
    return lines[Math.floor(Math.random() * lines.length)];
  }

  function compactSpeech(text) {
    const value = String(text || '').replace(/\s+/g, ' ').trim();
    if (!value) return '';
    if (value.length <= 18) return value;
    const cut = value.slice(0, 17).replace(/[，。、“”！？；：,\.\!\?]+$/g, '');
    return `${cut}…`;
  }

  function stateSpeech(pet) {
    if (!pet) return pickBubble('idle');
    if (pet.asleep) return compactSpeech(pet.blocked_reason || `${S.petName}先缓一缓。`);
    if (pet.hunger >= 88) return compactSpeech(`${S.petName}饿了，先喂我。`);
    if (pet.energy <= 10) return compactSpeech(`${S.petName}困了，先睡会儿。`);
    if (pet.hunger >= 70) return compactSpeech(`${S.petName}想先吃一点。`);
    if (pet.energy <= 24) return compactSpeech(`${S.petName}有点累了。`);
    return '';
  }

  function setSpeech(text, ticks) {
    const value = String(text || '').trim();
    if (!value) return;
    S.speech = value;
    S.speechTimer = ticks || 180;
    syncBubble();
  }

  function syncBubble() {
    if (bubbleMain) {
      bubbleMain.textContent = S.speech;
      bubbleMain.classList.toggle('show', S.speechTimer > 0 && !!S.speech);
    }
    if (bubbleCompact) {
      bubbleCompact.textContent = '';
      bubbleCompact.classList.remove('show');
    }
  }

  function configureCanvas(canvas, ctx, width, height) {
    if (!canvas || !ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function initBubbles() {
    bubbleMain = document.getElementById('pet-bubble-main');
    bubbleCompact = document.getElementById('pet-bubble-compact');
    if (!bubbleMain) {
      const stage = document.getElementById('avatar-stage');
      if (stage) {
        bubbleMain = document.createElement('div');
        bubbleMain.id = 'pet-bubble-main';
        bubbleMain.className = 'pet-bubble pet-bubble-main';
        stage.appendChild(bubbleMain);
      }
    }
    if (!bubbleCompact) {
      const face = document.querySelector('.compact-face');
      if (face) {
        bubbleCompact = document.createElement('div');
        bubbleCompact.id = 'pet-bubble-compact';
        bubbleCompact.className = 'pet-bubble pet-bubble-compact';
        face.appendChild(bubbleCompact);
      }
    }
    syncBubble();
  }

  function addParticles(type, count, anchorX, anchorY) {
    for (let i = 0; i < count; i++) {
      S.particles.push({
        type,
        x: anchorX + (Math.random() - 0.5) * 36,
        y: anchorY + (Math.random() - 0.5) * 24,
        vx: (Math.random() - 0.5) * 2.4,
        vy: -1.3 - Math.random() * 1.5,
        life: 1,
        size: 6 + Math.random() * 7,
      });
    }
  }

  function triggerMood(mood, ticks, speech) {
    S.mood = mood || 'idle';
    S.moodTimer = ticks || 160;
    if (speech) setSpeech(speech, Math.max(180, ticks || 160));
    else setSpeech(pickBubble(S.mood), Math.max(180, ticks || 160));
  }

  function updatePet(pet) {
    if (!pet) return;
    const prevAction = S.lastAction;
    const prevLevel = S.lastLevel;
    const prevStage = S.lastStage;
    S.species = pet.species_id || 'lobster';
    S.stage = pet.stage_id || 'seed';
    S.rarity = String(pet.rarity || 'common').toLowerCase();
    S.petName = pet.name || pet.pet_name || '伙伴';
    S.roleId = String(pet.role_id || 'companion');
    S.roleTitle = String(pet.role_title || '陪伴型');
    S.lastAction = String(pet.last_action || '');
    S.lastLevel = Number(pet.level || 1);
    S.lastStage = S.stage;
    if (prevAction && S.lastAction !== prevAction) {
      const actionMood = {
        feed: ['feed', '补给到位，我舒服多了。', 'heart'],
        play: ['play', '继续，我现在很来劲。', 'star'],
        nap: ['sleep', '我补个小觉。', 'zzz'],
        focus_companion: ['think', '我正盯着这条线索。', 'spark'],
        acknowledge_intro: ['happy', '认识啦，我会一直陪着你。', 'heart'],
        send_message: ['talk', '消息已经送出去了。', 'spark'],
        learn_request: ['think', '学习请求已经接住了。', 'spark'],
        reply_complete: ['happy', '真实回复回来了。', 'heart'],
      }[S.lastAction];
      if (actionMood) {
        triggerMood(actionMood[0], ['feed', 'play', 'nap'].includes(S.lastAction) ? 340 : 240, actionMood[1]);
        addParticles(actionMood[2], S.lastAction === 'play' ? 11 : 7, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.36);
      }
    }
    if (Number(pet.level || 1) > prevLevel || (prevStage && S.stage !== prevStage)) {
      triggerMood('happy', 300, S.stage !== prevStage ? `我进化到 ${pet.stage_title || S.stage} 了。` : `我升到 Lv.${pet.level || 1} 了。`);
      addParticles('spark', 10, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.32);
    }
    if (pet.asleep) {
      triggerMood('sleep', 260, pet.blocked_reason || '我先睡一下。');
      return;
    }
    if (pet.hunger >= 70) {
      setSpeech(stateSpeech(pet), 220);
      return;
    }
    if (pet.energy <= 24) {
      setSpeech(stateSpeech(pet), 220);
      return;
    }
    if (S.speechTimer <= 0) {
      S.speech = '';
      syncBubble();
    }
  }

  function patchCallbacks() {
    const baseUpdatePet = window.updatePet;
    if (typeof baseUpdatePet === 'function' && !baseUpdatePet.__canvasPatched) {
      const wrapped = function () {
        const result = baseUpdatePet.apply(this, arguments);
        const pet = arguments[0];
        const pendingReply = arguments[3];
        if (pet) updatePet(pet);
        if (pendingReply) triggerMood('think', 9999, '我正在等真实回复回来。');
        return result;
      };
      wrapped.__canvasPatched = true;
      window.updatePet = wrapped;
    }

    const baseAction = window.onActionResult;
    if (typeof baseAction === 'function' && !baseAction.__canvasPatched) {
      const wrappedAction = function (action, payload) {
        const result = baseAction.apply(this, arguments);
        const map = {
          feed: { mood: 'feed', speech: '补给到位，我舒服多了。', particles: 'heart' },
          play: { mood: 'play', speech: '继续，我现在很来劲。', particles: 'star' },
          nap: { mood: 'sleep', speech: '我补个小觉。', particles: 'zzz' },
          learn: { mood: 'think', speech: '这条我已经接入学习流。', particles: 'spark' },
          send: { mood: 'talk', speech: payload?.ok ? '消息已经替你送出去了。' : '我没找到会话入口。', particles: payload?.ok ? 'spark' : 'heart' },
          screenshot: { mood: 'think', speech: '画面我收到了，等你继续。', particles: 'spark' },
        };
        const item = map[action];
        if (payload?.pet) updatePet(payload.pet);
        if (item) {
          const duration = ['feed', 'play', 'nap'].includes(action) ? 340 : action === 'learn' && payload?.pending_reply ? 9999 : 260;
          const speech = payload?.message || item.speech;
          triggerMood(item.mood, duration, speech);
          addParticles(item.particles, action === 'play' ? 11 : action === 'nap' ? 7 : 8, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.38);
        }
        return result;
      };
      wrappedAction.__canvasPatched = true;
      window.onActionResult = wrappedAction;
    }

    const baseReply = window.onReplyResult;
    if (typeof baseReply === 'function' && !baseReply.__canvasPatched) {
      const wrappedReply = function (payload) {
        const result = baseReply.apply(this, arguments);
        triggerMood('happy', 240, '回复回来了，我给你带回来了。');
        addParticles('heart', 7, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.34);
        if (payload?.pet) updatePet(payload.pet);
        return result;
      };
      wrappedReply.__canvasPatched = true;
      window.onReplyResult = wrappedReply;
    }
  }

  function initEvents() {
    const stage = document.getElementById('avatar-stage');
    if (stage) {
      stage.addEventListener('mousemove', (event) => {
        const rect = stage.getBoundingClientRect();
        const nx = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        const ny = ((event.clientY - rect.top) / rect.height) * 2 - 1;
        S.pointerX = Math.max(-1, Math.min(1, nx));
        S.pointerY = Math.max(-1, Math.min(1, ny));
      });
      stage.addEventListener('mouseleave', () => {
        S.pointerX = 0;
        S.pointerY = 0;
      });
      stage.addEventListener('click', () => {
        addParticles('heart', 6, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.36);
        triggerMood('happy', 180, ['摸摸收到。', '我也喜欢这样。', '嘿，我会记住的。'][Math.floor(Math.random() * 3)]);
      });
    }
    if (compactCanvas) {
      compactCanvas.addEventListener('click', (event) => {
        event.stopPropagation();
        addParticles('heart', 4, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.38);
        setSpeech(compactSpeech(pickBubble('happy')), 160);
      });
    }
  }

  function init() {
    mainCanvas = document.getElementById('pet-canvas-main');
    compactCanvas = document.getElementById('pet-canvas-compact');
    if (!mainCanvas || !compactCanvas) return;

    mainCtx = mainCanvas.getContext('2d');
    compactCtx = compactCanvas.getContext('2d');
    configureCanvas(mainCanvas, mainCtx, MAIN_SIZE.width, MAIN_SIZE.height);
    configureCanvas(compactCanvas, compactCtx, COMPACT_SIZE.width, COMPACT_SIZE.height);
    initBubbles();
    initEvents();
    patchCallbacks();
    if (!S.running) {
      S.running = true;
      requestAnimationFrame(loop);
    }
  }

  function loop() {
    S.tick += 1;
    if (S.moodTimer > 0) S.moodTimer -= 1;
    else S.mood = 'idle';
    if (S.speechTimer > 0) S.speechTimer -= 1;
    syncBubble();

    S.blink = Math.max(0, S.blink - 0.12);
    if (S.blink === 0 && Math.random() < 0.006) S.blink = 1;
    S.eyeX += (S.pointerX * 4 - S.eyeX) * 0.1;
    S.eyeY += (S.pointerY * 2.8 - S.eyeY) * 0.1;
    S.glowPulse = 0.5 + Math.sin(S.tick * 0.05) * 0.5;

    drawScene(mainCtx, MAIN_SIZE.width, MAIN_SIZE.height, false);
    drawScene(compactCtx, COMPACT_SIZE.width, COMPACT_SIZE.height, true);
    requestAnimationFrame(loop);
  }

  function withRenderState(renderState, fn) {
    const snapshot = {
      species: S.species,
      stage: S.stage,
      mood: S.mood,
      tick: S.tick,
      blink: S.blink,
      eyeX: S.eyeX,
      eyeY: S.eyeY,
      glowPulse: S.glowPulse,
    };
    S.species = renderState.species;
    S.stage = renderState.stage;
    S.mood = renderState.mood;
    S.tick = renderState.tick;
    S.blink = renderState.blink;
    S.eyeX = renderState.eyeX;
    S.eyeY = renderState.eyeY;
    S.glowPulse = renderState.glowPulse;
    try {
      fn();
    } finally {
      S.species = snapshot.species;
      S.stage = snapshot.stage;
      S.mood = snapshot.mood;
      S.tick = snapshot.tick;
      S.blink = snapshot.blink;
      S.eyeX = snapshot.eyeX;
      S.eyeY = snapshot.eyeY;
      S.glowPulse = snapshot.glowPulse;
    }
  }

  function sceneOffsets(compact) {
    const m = S.mood;
    return {
      breath: Math.sin(S.tick * (compact ? 0.08 : 0.06)) * (compact ? 1.8 : 3.3),
      sway: Math.sin(S.tick * (m === 'play' ? 0.18 : 0.05)) * (compact ? 1.4 : 2.8),
      lift: m === 'play' ? Math.abs(Math.sin(S.tick * 0.18)) * (compact ? 3.5 : 8) : 0,
      drowse: m === 'sleep' ? Math.sin(S.tick * 0.03) * (compact ? 0.6 : 1.4) : 0,
    };
  }

  function drawScene(ctx, width, height, compact) {
    if (!ctx) return;
    drawSceneForState(ctx, width, height, compact, !compact);
  }

  function drawSceneForState(ctx, width, height, compact, includeParticles) {
    const spec = stageSpec(S.species, S.stage);
    const offsets = sceneOffsets(compact);
    ctx.clearRect(0, 0, width, height);
    drawBackdrop(ctx, width, height, spec, compact);

    ctx.save();
    const scale = compact ? 0.31 : 0.95;
    const x = width * 0.5 + offsets.sway;
    const y = compact ? height * 0.62 + offsets.drowse : height * 0.62 + offsets.breath + offsets.drowse - offsets.lift * 0.2;
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    if (S.species === 'sprite') drawSprite(ctx, spec, compact);
    else if (S.species === 'mecha') drawMecha(ctx, spec, compact);
    else if (S.species === 'moth') drawMoth(ctx, spec, compact);
    else if (S.species === 'slime') drawSlime(ctx, spec, compact);
    else if (S.species === 'avian') drawAvian(ctx, spec, compact);
    else drawLobster(ctx, spec, compact);
    ctx.restore();

    if (includeParticles) drawParticles(ctx);
  }

  function renderPreview(canvasOrId, pet, options) {
    const target = typeof canvasOrId === 'string' ? document.getElementById(canvasOrId) : canvasOrId;
    if (!target || !pet) return;
    const ctx = target.getContext('2d');
    if (!ctx) return;
    const opts = options || {};
    const width = Number(opts.width || target.getAttribute('width') || target.clientWidth || 132);
    const height = Number(opts.height || target.getAttribute('height') || target.clientHeight || 132);
    const compact = !!opts.compact;
    configureCanvas(target, ctx, width, height);
    const renderState = {
      species: pet.species_id || 'lobster',
      stage: pet.stage_id || 'seed',
      mood: opts.mood || (pet.asleep ? 'sleep' : 'idle'),
      tick: Number(opts.tick ?? 42),
      blink: 0,
      eyeX: Number(opts.eyeX ?? 0.9),
      eyeY: Number(opts.eyeY ?? 0.4),
      glowPulse: 0.85,
    };
    withRenderState(renderState, () => {
      drawSceneForState(ctx, width, height, compact, false);
    });
  }

  function drawBackdrop(ctx, width, height, spec, compact) {
    const { aura, accent, shell } = spec.palette;
    const g = ctx.createRadialGradient(width * 0.52, height * 0.4, 10, width * 0.52, height * 0.46, compact ? 54 : 110);
    g.addColorStop(0, aura.replace(/\.([0-9]+)\)/, '.38)'));
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, width, height);

    ctx.save();
    ctx.globalAlpha = compact ? 0.18 : 0.26;
    ctx.fillStyle = shell;
    ctx.beginPath();
    ctx.ellipse(width * 0.5, compact ? height * 0.84 : height * 0.88, compact ? 17 : 46, compact ? 5 : 10, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    if (!compact) {
      ctx.save();
      ctx.globalAlpha = 0.35 + S.glowPulse * 0.18;
      ctx.strokeStyle = accent;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.arc(width * 0.5, height * 0.42, 72 + Math.sin(S.tick * 0.03) * 3, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }

  function drawEye(ctx, x, y, lineColor, glowColor, compact) {
    if (S.mood === 'sleep') {
      ctx.strokeStyle = lineColor;
      ctx.lineWidth = compact ? 2.5 : 2;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.arc(x, y, compact ? 8 : 7, Math.PI * 0.1, Math.PI * 0.9);
      ctx.stroke();
      return;
    }
    const blinkScale = Math.max(0.08, 1 - S.blink * 0.9);
    ctx.save();
    ctx.translate(x + S.eyeX * 0.45, y + S.eyeY * 0.45);
    ctx.scale(1, blinkScale);
    ctx.shadowColor = 'rgba(255,255,255,0.45)';
    ctx.shadowBlur = compact ? 4 : 6;
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.ellipse(0, 0, compact ? 5.8 : 5.2, compact ? 6.9 : 6.3, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.fillStyle = lineColor;
    ctx.beginPath();
    ctx.ellipse(0, 1.1, compact ? 2.6 : 2.5, compact ? 3.4 : 3.35, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(1.35, -1.55, compact ? 1.05 : 0.95, 0, Math.PI * 2);
    ctx.fill();
    if (glowColor) {
      ctx.globalAlpha = 0.55 + S.glowPulse * 0.25;
      ctx.strokeStyle = glowColor;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.arc(0, 0.2, compact ? 6.1 : 5.4, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawMouth(ctx, x, y, color, compact) {
    ctx.strokeStyle = color;
    ctx.lineWidth = compact ? 2.8 : 2;
    ctx.lineCap = 'round';
    ctx.beginPath();
    if (S.mood === 'think') {
      ctx.moveTo(x - 4, y + 1);
      ctx.lineTo(x + 4, y + 1);
    } else if (S.mood === 'play' || S.mood === 'happy' || S.mood === 'feed') {
      ctx.arc(x, y - 1, compact ? 6 : 5, 0.1, Math.PI - 0.1, false);
    } else if (S.mood === 'talk') {
      const open = 2 + Math.abs(Math.sin(S.tick * 0.22)) * 3;
      ctx.ellipse(x, y + 2, compact ? 4.6 : 4.2, open, 0, 0, Math.PI * 2);
    } else {
      ctx.arc(x, y + 2, compact ? 5 : 4, Math.PI * 0.18, Math.PI * 0.82, true);
    }
    ctx.stroke();
  }

  function drawParticles(ctx) {
    S.particles = S.particles.filter((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.018;
      if (p.life <= 0) return false;
      ctx.save();
      ctx.globalAlpha = p.life;
      if (p.type === 'heart') drawHeart(ctx, p.x, p.y, p.size, '#f1726a');
      else if (p.type === 'star') drawStar(ctx, p.x, p.y, p.size, '#ffc45b');
      else if (p.type === 'zzz') {
        ctx.fillStyle = '#8ca3d7';
        ctx.font = `bold ${Math.round(p.size + 4)}px sans-serif`;
        ctx.fillText('z', p.x, p.y);
      } else {
        drawStar(ctx, p.x, p.y, p.size * 0.7, '#8fe4ff');
      }
      ctx.restore();
      return true;
    });
  }

  function drawHeart(ctx, x, y, size, color) {
    const s = size * 0.55;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x, y + s * 0.4);
    ctx.bezierCurveTo(x, y - s * 0.3, x - s, y - s * 0.25, x - s, y + s * 0.15);
    ctx.bezierCurveTo(x - s, y + s * 0.72, x, y + s * 1.12, x, y + s * 1.12);
    ctx.bezierCurveTo(x, y + s * 1.12, x + s, y + s * 0.72, x + s, y + s * 0.15);
    ctx.bezierCurveTo(x + s, y - s * 0.25, x, y - s * 0.3, x, y + s * 0.4);
    ctx.fill();
  }

  function drawStar(ctx, x, y, size, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.lineCap = 'round';
    ctx.beginPath();
    for (let i = 0; i < 4; i++) {
      const a = (Math.PI / 2) * i;
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a) * size, y + Math.sin(a) * size);
    }
    ctx.stroke();
  }

  function ellipseFill(ctx, x, y, rx, ry, colors, rotation) {
    const g = ctx.createLinearGradient(x - rx, y - ry, x + rx, y + ry);
    g.addColorStop(0, colors[0]);
    g.addColorStop(0.58, colors[1]);
    g.addColorStop(1, colors[2] || colors[1]);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, rotation || 0, 0, Math.PI * 2);
    ctx.fill();
  }

  function softStroke(ctx, color, width) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
  }

  function addGloss(ctx, x, y, rx, ry) {
    ctx.save();
    ctx.globalAlpha = 0.34;
    const g = ctx.createLinearGradient(x - rx, y - ry, x + rx, y + ry);
    g.addColorStop(0, 'rgba(255,255,255,0.95)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x - rx * 0.18, y - ry * 0.3, rx * 0.42, ry * 0.2, -0.35, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function addShadowOval(ctx, x, y, rx, ry, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = '#5f3426';
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawBlush(ctx, leftX, rightX, y, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha || 0.18;
    ctx.fillStyle = '#ffb4be';
    ctx.beginPath();
    ctx.ellipse(leftX, y, 4.4, 2.7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(rightX, y, 4.4, 2.7, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawLobster(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const playKick = S.mood === 'play' ? Math.sin(S.tick * 0.22) * 9 : Math.sin(S.tick * 0.07) * 3;
    const talkWave = S.mood === 'talk' ? Math.sin(S.tick * 0.18) * 7 : 0;

    drawLobsterAura(ctx, B, P, compact);
    drawLobsterFeelers(ctx, B, P);
    drawLobsterLegs(ctx, B, P, compact);
    drawLobsterClaw(ctx, -B.claws, -4 + playKick, 1, B, P);
    drawLobsterClaw(ctx, B.claws, -4 + talkWave, -1, B, P);
    drawLobsterTail(ctx, B, P);

    addShadowOval(ctx, 0, 8, B.rx * 0.9, B.ry * 0.82, compact ? 0.08 : 0.11);
    ellipseFill(ctx, 0, 0, B.rx, B.ry, [P.accent, P.body, P.shell], 0);
    softStroke(ctx, P.line, compact ? 2.6 : 1.9);
    ctx.beginPath();
    ctx.ellipse(0, 0, B.rx, B.ry, 0, 0, Math.PI * 2);
    ctx.stroke();

    ellipseFill(ctx, 0, -6, B.rx - 8, B.shellRy, [P.accent, P.shell, P.line], 0);

    if (B.spikes) {
      for (let i = 0; i < B.spikes; i++) {
        const px = -14 + i * 10;
        drawDiamond(ctx, px, -B.ry + 5 - Math.abs(Math.sin(S.tick * 0.03 + i)) * 2, 4.2 + i * 0.28, P.accent, P.line);
      }
    }

    if (B.crest) {
      drawCrown(ctx, B, P);
    }

    ellipseFill(ctx, 0, 10, B.rx - 14, B.ry - 13, ['#fff8f1', P.belly, 'rgba(255,214,194,.82)'], 0);
    addGloss(ctx, 0, 0, B.rx, B.ry);

    ctx.strokeStyle = 'rgba(255,255,255,.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(-10, -12, 10, 5, -0.3, 0, Math.PI * 2);
    ctx.stroke();

    drawEye(ctx, -12, -8, P.line, B.eyeGlow ? P.accent : '', compact);
    drawEye(ctx, 12, -8, P.line, B.eyeGlow ? P.accent : '', compact);
    drawBlush(ctx, -19, 19, 2, compact ? 0.12 : 0.16);
    if (B.eyeGlow) {
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(-18, -16);
      ctx.lineTo(-7, -13);
      ctx.moveTo(18, -16);
      ctx.lineTo(7, -13);
      ctx.stroke();
    }
    drawMouth(ctx, 0, 13, P.line, compact);
  }

  function drawLobsterAura(ctx, B, P, compact) {
    if (!B.ring && !B.fins) return;
    ctx.save();
    ctx.globalAlpha = compact ? 0.3 : 0.45;
    if (B.ring) {
      for (let i = 0; i < B.ring; i++) {
        ctx.strokeStyle = P.accent;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.ellipse(0, -4, B.rx + 8 + i * 7, B.ry + 8 + i * 4, 0, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    if (B.fins) {
      for (let i = 0; i < B.fins; i++) {
        const dir = i % 2 === 0 ? -1 : 1;
        drawDiamond(ctx, dir * (B.rx + 10 + i), -4 + i * 6, 4 + i * 0.6, P.accent, '');
      }
    }
    ctx.restore();
  }

  function drawLobsterFeelers(ctx, B, P) {
    const swing = Math.sin(S.tick * (S.mood === 'think' ? 0.14 : 0.07)) * 4;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    [[-12, -B.whisker, -1], [12, B.whisker, 1]].forEach(([sx, ex, dir]) => {
      ctx.beginPath();
      ctx.moveTo(sx, -26);
      ctx.quadraticCurveTo(sx + dir * 8, -44 + swing * dir, ex, -58 + swing * dir);
      ctx.stroke();
      ctx.fillStyle = P.accent;
      for (let i = 0; i < B.whiskerBulbs; i++) {
        ctx.beginPath();
        ctx.arc(ex - dir * i * 4, -58 + swing * dir - i * 3, 3.4 - i * 0.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }

  function drawLobsterLegs(ctx, B, P, compact) {
    const step = S.mood === 'play' ? Math.sin(S.tick * 0.26) * 0.35 : Math.sin(S.tick * 0.08) * 0.12;
    ctx.strokeStyle = P.shell;
    ctx.lineWidth = compact ? 3.2 : 2.8;
    ctx.lineCap = 'round';
    for (let i = 0; i < B.legs; i++) {
      const offset = -20 + i * 10;
      const len = 16 + i * 2;
      [[-1, offset], [1, -offset]].forEach(([dir, side]) => {
        ctx.save();
        ctx.translate(dir * (B.rx - 7), 14 + i * 4);
        ctx.rotate((dir === -1 ? -1 : 1) * (0.5 + step + i * 0.04));
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(dir * len * 0.55, len * 0.6);
        ctx.lineTo(dir * len, len);
        ctx.stroke();
        ctx.restore();
      });
    }
  }

  function drawLobsterClaw(ctx, x, y, dir, B, P) {
    const open = S.mood === 'feed' ? 0.75 : S.mood === 'play' ? 0.88 : S.mood === 'talk' ? 0.42 : 0.22;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(dir, 1);
    softStroke(ctx, P.line, 1.8);
    ctx.beginPath();
    ctx.moveTo(-6, -1);
    ctx.quadraticCurveTo(-18, 2, -26, 9);
    ctx.stroke();
    ellipseFill(ctx, 0, 0, 13, 10.5, ['#fff4ea', P.body, P.shell], -0.2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(9, -1);
    ctx.quadraticCurveTo(17, -9 - open * 5, 21, -10 - open * 8);
    ctx.lineTo(18, -2);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(9, 4);
    ctx.quadraticCurveTo(18, 10 + open * 4, 22, 11 + open * 8);
    ctx.lineTo(17, 8);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawLobsterTail(ctx, B, P) {
    ctx.fillStyle = P.shell;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 2;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.ellipse(0, 20 + i * 7, B.tail + 4 - i * 2, 5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
  }

  function drawCrown(ctx, B, P) {
    ctx.fillStyle = P.accent;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(-14, -B.ry + 2);
    ctx.lineTo(-6, -B.ry - B.crest);
    ctx.lineTo(0, -B.ry + 1 - B.crest * 0.35);
    ctx.lineTo(7, -B.ry - B.crest * 0.85);
    ctx.lineTo(16, -B.ry + 1);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  function drawSprite(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const wingFlap = Math.sin(S.tick * (S.mood === 'play' ? 0.3 : 0.12)) * 10;
    const haloSpin = S.tick * 0.01;

    ctx.save();
    ctx.rotate(Math.sin(S.tick * 0.04) * 0.06);
    drawSpriteHalo(ctx, B, P, haloSpin, compact);
    drawSpriteWings(ctx, B, P, wingFlap);
    drawSpriteAntenna(ctx, B, P);

    addShadowOval(ctx, 0, 10, B.rx * 0.76, B.ry * 0.52, compact ? 0.06 : 0.09);
    const bodyGrad = ctx.createLinearGradient(-B.rx, -B.ry, B.rx, B.ry + 14);
    bodyGrad.addColorStop(0, '#ffffff');
    bodyGrad.addColorStop(0.32, P.shell);
    bodyGrad.addColorStop(0.72, P.body);
    bodyGrad.addColorStop(1, P.line);
    ctx.fillStyle = bodyGrad;
    ctx.beginPath();
    ctx.moveTo(0, -B.ry);
    ctx.bezierCurveTo(B.rx, -B.ry + 8, B.rx + 8, B.ry - 10, 0, B.ry + 10);
    ctx.bezierCurveTo(-B.rx - 8, B.ry - 10, -B.rx, -B.ry + 8, 0, -B.ry);
    ctx.fill();
    softStroke(ctx, P.line, compact ? 2.6 : 1.8);
    ctx.stroke();

    ellipseFill(ctx, 0, -4, B.rx - 5, B.ry - 8, ['rgba(255,255,255,.98)', P.shell, P.body], 0);
    if (B.gown) drawSpriteGown(ctx, B, P);
    addGloss(ctx, 0, -2, B.rx - 3, B.ry - 4);

    drawSpriteTail(ctx, B, P);
    drawSpriteFringe(ctx, B, P);
    drawEye(ctx, -10, -6, P.line, P.accent, compact);
    drawEye(ctx, 10, -6, P.line, P.accent, compact);
    drawBlush(ctx, -17, 17, 2, compact ? 0.11 : 0.15);
    drawMouth(ctx, 0, 12, P.line, compact);

    if (S.mood === 'think') {
      for (let i = 0; i < 3; i++) drawDiamond(ctx, -7 + i * 7, 3, 2.8, i < (Math.floor(S.tick / 18) % 3) + 1 ? P.accent : 'rgba(108,83,183,.22)', '');
    }
    ctx.restore();
  }

  function drawSpriteHalo(ctx, B, P, haloSpin, compact) {
    ctx.save();
    ctx.rotate(haloSpin);
    ctx.strokeStyle = P.accent;
    ctx.globalAlpha = 0.55 + S.glowPulse * 0.2;
    ctx.lineWidth = compact ? 2.2 : 1.8;
    for (let i = 0; i <= B.orbitals; i++) {
      ctx.beginPath();
      ctx.ellipse(0, -2, B.rx + B.halo + i * 4, B.ry + B.halo * 0.4 + i * 2, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    for (let i = 0; i < B.shards; i++) {
      const a = (Math.PI * 2 * i) / B.shards;
      drawDiamond(ctx, Math.cos(a) * (B.rx + B.halo), Math.sin(a) * (B.ry + B.halo * 0.45) - 2, 4 + i * 0.4, P.accent, '');
    }
    if (B.orbitals) {
      for (let i = 0; i < B.orbitals; i++) {
        const a = haloSpin * 5 + (Math.PI * 2 * i) / B.orbitals;
        drawDiamond(ctx, Math.cos(a) * (B.rx + B.halo + 8), Math.sin(a) * (B.ry * 0.5 + B.halo * 0.25) - 3, 3.4, '#ffffff', '');
      }
    }
    ctx.restore();
  }

  function drawSpriteWings(ctx, B, P, flap) {
    softStroke(ctx, 'rgba(114,88,184,.45)', 1.2);
    const layers = B.wings;
    for (let i = 0; i < layers; i++) {
      const offsetY = -8 + i * 8;
      const size = 20 + i * 6;
      [[-1, -1], [1, 1]].forEach(([dir]) => {
        ctx.save();
        ctx.translate(dir * (B.rx - 3), offsetY);
        ctx.rotate(dir * (0.28 + flap * 0.01));
        const wingGrad = ctx.createLinearGradient(0, -size * 0.4, dir * (size + 9), size * 0.9);
        wingGrad.addColorStop(0, 'rgba(255,255,255,.92)');
        wingGrad.addColorStop(0.45, P.shell);
        wingGrad.addColorStop(1, 'rgba(255,255,255,.18)');
        ctx.fillStyle = wingGrad;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(dir * size, -size * 0.36, dir * (size + 9), 4);
        ctx.quadraticCurveTo(dir * size, size * 0.72, 0, 8);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
      });
    }
  }

  function drawSpriteTail(ctx, B, P) {
    ctx.fillStyle = P.accent;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 3; i++) {
      drawDiamond(ctx, 0, B.ry + 6 + i * 8, B.tail - i * 2, P.accent, P.line);
    }
  }

  function drawSpriteFringe(ctx, B, P) {
    ctx.fillStyle = P.accent;
    for (let i = 0; i < B.fringe; i++) {
      const x = -12 + i * 8;
      drawDiamond(ctx, x, -B.ry + 8 + Math.sin(S.tick * 0.05 + i) * 2, 4.5, P.accent, '');
    }
    if (B.crown) {
      drawDiamond(ctx, 0, -B.ry - 2, 6 + B.crown * 0.2, '#fff4b8', P.line);
    }
  }

  function drawSpriteGown(ctx, B, P) {
    ctx.save();
    ctx.globalAlpha = 0.28 + B.gown * 0.08;
    const skirt = ctx.createLinearGradient(0, 10, 0, B.ry + 24);
    skirt.addColorStop(0, 'rgba(255,255,255,.72)');
    skirt.addColorStop(1, P.accent);
    ctx.fillStyle = skirt;
    ctx.beginPath();
    ctx.moveTo(-B.rx + 4, 8);
    ctx.quadraticCurveTo(0, B.ry + 16 + B.gown * 3, B.rx - 4, 8);
    ctx.quadraticCurveTo(0, 18, -B.rx + 4, 8);
    ctx.fill();
    ctx.restore();
  }

  function drawSpriteAntenna(ctx, B, P) {
    if (!B.antenna) return;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.4;
    for (let i = 0; i < B.antenna; i++) {
      const dir = i % 2 === 0 ? -1 : 1;
      ctx.beginPath();
      ctx.moveTo(dir * 7, -B.ry + 7);
      ctx.quadraticCurveTo(dir * (12 + i * 2), -B.ry - 10 - i * 2, dir * (16 + i * 2), -B.ry - 18 - i * 3);
      ctx.stroke();
      drawDiamond(ctx, dir * (16 + i * 2), -B.ry - 18 - i * 3, 2.8 + i * 0.4, P.accent, '');
    }
  }

  function drawMoth(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const flap = Math.sin(S.tick * (S.mood === 'play' ? 0.22 : 0.09)) * (8 + B.wings * 1.6);
    const drift = Math.sin(S.tick * 0.05) * 4;

    ctx.save();
    ctx.rotate(Math.sin(S.tick * 0.03) * 0.05);
    drawMothDust(ctx, B, P);
    drawMothWings(ctx, B, P, flap);
    drawMothAntenna(ctx, B, P);
    drawMothTail(ctx, B, P);

    addShadowOval(ctx, 0, 12, B.rx * 0.8, B.ry * 0.5, compact ? 0.05 : 0.08);
    ellipseFill(ctx, 0, 2, B.rx, B.ry, ['#fffdf9', P.shell, P.body], 0);
    softStroke(ctx, P.line, compact ? 2.5 : 1.8);
    ctx.beginPath();
    ctx.ellipse(0, 2, B.rx, B.ry, 0, 0, Math.PI * 2);
    ctx.stroke();
    ellipseFill(ctx, 0, -2, B.rx - 7, B.ry - 9, ['rgba(255,255,255,.98)', P.belly, P.shell], 0);
    addGloss(ctx, 0, -2, B.rx, B.ry);

    if (B.crescent) {
      ctx.save();
      ctx.globalAlpha = 0.45;
      ctx.strokeStyle = P.accent;
      ctx.lineWidth = 1.4;
      for (let i = 0; i < B.crescent; i++) {
        ctx.beginPath();
        ctx.arc(0, -B.ry - 3 - i * 3, 8 + i * 2, Math.PI * 0.15, Math.PI * 0.85);
        ctx.stroke();
      }
      ctx.restore();
    }

    if (B.crown) drawDiamond(ctx, 0, -B.ry - 6, 4 + B.crown, P.accent, P.line);

    drawEye(ctx, -9, -7 + drift * 0.04, P.line, P.accent, compact);
    drawEye(ctx, 9, -7 - drift * 0.04, P.line, P.accent, compact);
    drawBlush(ctx, -15, 15, 2, compact ? 0.1 : 0.13);
    drawMouth(ctx, 0, 12, P.line, compact);
    ctx.restore();
  }

  function drawMothWings(ctx, B, P, flap) {
    const layers = B.wings;
    for (let i = 0; i < layers; i++) {
      const span = B.wingSpan + i * 5;
      const lift = i * 4;
      [[-1], [1]].forEach(([dir]) => {
        ctx.save();
        ctx.translate(dir * (B.rx - 3), -6 + lift);
        ctx.rotate(dir * (0.34 + flap * 0.01));
        const wingGrad = ctx.createLinearGradient(0, -span * 0.5, dir * (span + 8), span);
        wingGrad.addColorStop(0, 'rgba(255,255,255,.95)');
        wingGrad.addColorStop(0.45, P.shell);
        wingGrad.addColorStop(1, P.body);
        ctx.fillStyle = wingGrad;
        softStroke(ctx, P.line, 1.15);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(dir * (span * 0.65), -span * 0.4, dir * (span + 6), 4);
        ctx.quadraticCurveTo(dir * (span * 0.72), span * 0.7, 0, 12);
        ctx.quadraticCurveTo(dir * (span * 0.18), 6, 0, 0);
        ctx.fill();
        ctx.stroke();
        ctx.restore();
      });
    }
  }

  function drawMothAntenna(ctx, B, P) {
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.4;
    [[-1], [1]].forEach(([dir], idx) => {
      ctx.beginPath();
      ctx.moveTo(dir * 5, -B.ry + 4);
      ctx.quadraticCurveTo(dir * (11 + idx), -B.ry - 12, dir * (16 + B.antenna * 2), -B.ry - 18);
      ctx.stroke();
      drawDiamond(ctx, dir * (16 + B.antenna * 2), -B.ry - 18, 2.6 + B.antenna * 0.4, P.accent, '');
    });
  }

  function drawMothTail(ctx, B, P) {
    for (let i = 0; i < 3; i++) {
      drawDiamond(ctx, 0, B.ry + i * 7, B.tail - i * 2, i === 2 ? P.accent : P.shell, P.line);
    }
  }

  function drawMothDust(ctx, B, P) {
    ctx.save();
    ctx.globalAlpha = 0.3 + S.glowPulse * 0.12;
    for (let i = 0; i < B.dust; i++) {
      const a = S.tick * 0.03 + (Math.PI * 2 * i) / B.dust;
      drawDiamond(ctx, Math.cos(a) * (B.rx + 15), Math.sin(a) * (B.ry * 0.4 + 10) - 10, 2.8 + i * 0.5, P.accent, '');
    }
    ctx.restore();
  }

  function drawSlime(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const wobble = Math.sin(S.tick * 0.08) * B.wobble;

    ctx.save();
    drawSlimeHalo(ctx, B, P);
    addShadowOval(ctx, 0, 15, B.rx * 0.9, B.ry * 0.42, compact ? 0.06 : 0.09);
    ctx.beginPath();
    ctx.moveTo(-B.rx, -8);
    ctx.quadraticCurveTo(-B.rx - wobble * 0.4, B.ry - 18, -B.rx + 6, B.ry);
    ctx.quadraticCurveTo(-8, B.ry + 12 + wobble * 0.3, 0, B.ry + 10);
    ctx.quadraticCurveTo(10, B.ry + 13 - wobble * 0.2, B.rx - 5, B.ry);
    ctx.quadraticCurveTo(B.rx + wobble * 0.4, B.ry - 14, B.rx, -8);
    ctx.quadraticCurveTo(B.rx - 8, -B.ry, 0, -B.ry + 2);
    ctx.quadraticCurveTo(-B.rx + 8, -B.ry + 1, -B.rx, -8);
    const slimeGrad = ctx.createLinearGradient(-B.rx, -B.ry, B.rx, B.ry + 18);
    slimeGrad.addColorStop(0, '#ffffff');
    slimeGrad.addColorStop(0.35, P.shell);
    slimeGrad.addColorStop(1, P.body);
    ctx.fillStyle = slimeGrad;
    ctx.fill();
    softStroke(ctx, P.line, compact ? 2.5 : 1.8);
    ctx.stroke();

    ellipseFill(ctx, 0, 2, B.rx - 7, B.ry - 10, ['rgba(255,255,255,.95)', P.belly, P.shell], 0);
    addGloss(ctx, -2, -5, B.rx - 3, B.ry - 8);
    drawSlimeBuds(ctx, B, P);
    drawEye(ctx, -11, -6, P.line, P.accent, compact);
    drawEye(ctx, 11, -6, P.line, P.accent, compact);
    drawBlush(ctx, -17, 17, 1, compact ? 0.1 : 0.14);
    drawMouth(ctx, 0, 12, P.line, compact);
    ctx.fillStyle = P.accent;
    ctx.globalAlpha = 0.32 + S.glowPulse * 0.16;
    ctx.beginPath();
    ctx.arc(0, 1, B.core, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawSlimeHalo(ctx, B, P) {
    if (!B.halo) return;
    ctx.save();
    ctx.globalAlpha = 0.28 + S.glowPulse * 0.16;
    ctx.strokeStyle = P.accent;
    ctx.lineWidth = 1.4;
    for (let i = 0; i < B.halo; i++) {
      ctx.beginPath();
      ctx.ellipse(0, 2, B.rx + 7 + i * 6, B.ry + 4 + i * 3, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawSlimeBuds(ctx, B, P) {
    for (let i = 0; i < B.buds; i++) {
      const dir = i % 2 === 0 ? -1 : 1;
      ctx.beginPath();
      ctx.ellipse(dir * (12 + i * 5), -B.ry + 10 + i * 2, 6 + i, 8 + i, dir * 0.2, 0, Math.PI * 2);
      ctx.fillStyle = P.shell;
      ctx.fill();
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
    for (let i = 0; i < B.droplets; i++) {
      drawDiamond(ctx, -14 + i * 9, B.ry - 4 + Math.sin(S.tick * 0.05 + i) * 2, 3 + i * 0.4, P.accent, '');
    }
  }

  function drawAvian(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const wing = Math.sin(S.tick * (S.mood === 'play' ? 0.28 : 0.12)) * 12;

    ctx.save();
    drawAvianOrbit(ctx, B, P);
    drawAvianWings(ctx, B, P, wing);
    drawAvianTail(ctx, B, P);
    addShadowOval(ctx, 0, 15, B.rx * 0.86, B.ry * 0.45, compact ? 0.05 : 0.08);

    ellipseFill(ctx, 0, 2, B.rx, B.ry, ['#ffffff', P.shell, P.body], 0);
    softStroke(ctx, P.line, compact ? 2.5 : 1.8);
    ctx.beginPath();
    ctx.ellipse(0, 2, B.rx, B.ry, 0, 0, Math.PI * 2);
    ctx.stroke();
    ellipseFill(ctx, 0, 6, B.rx - 8, B.ry - 12, ['rgba(255,255,255,.98)', P.belly, P.shell], 0);
    addGloss(ctx, 0, -3, B.rx, B.ry);

    if (B.crest) {
      for (let i = 0; i < B.crest; i++) {
        drawDiamond(ctx, -6 + i * 6, -B.ry - 2 - i, 3.6 + i * 0.2, P.accent, P.line);
      }
    }

    ctx.fillStyle = P.accent;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(0, 1);
    ctx.lineTo(B.beak, 5);
    ctx.lineTo(0, 8);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    drawEye(ctx, -8, -7, P.line, P.accent, compact);
    drawEye(ctx, 8, -7, P.line, P.accent, compact);
    drawBlush(ctx, -14, 14, 2, compact ? 0.08 : 0.12);
    drawMouth(ctx, -1, 12, P.line, compact);
    ctx.restore();
  }

  function drawAvianWings(ctx, B, P, wing) {
    [[-1], [1]].forEach(([dir], idx) => {
      ctx.save();
      ctx.translate(dir * (B.rx - 4), 5);
      ctx.rotate(dir * (0.35 + wing * 0.008));
      const wingGrad = ctx.createLinearGradient(0, -16, dir * 28, 20);
      wingGrad.addColorStop(0, '#ffffff');
      wingGrad.addColorStop(0.5, P.shell);
      wingGrad.addColorStop(1, P.body);
      ctx.fillStyle = wingGrad;
      softStroke(ctx, P.line, 1.2);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.quadraticCurveTo(dir * (18 + B.wingLift * 3), -16, dir * (26 + idx * 2), 4);
      ctx.quadraticCurveTo(dir * 18, 20, 0, 10);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    });
  }

  function drawAvianTail(ctx, B, P) {
    for (let i = 0; i < B.tail; i++) {
      const dir = i % 2 === 0 ? -1 : 1;
      drawDiamond(ctx, dir * (2 + i * 2), B.ry + 5 + i * 3, 4 + Math.max(0, B.tail - i), P.accent, P.line);
    }
  }

  function drawAvianOrbit(ctx, B, P) {
    if (!B.orbit) return;
    ctx.save();
    ctx.globalAlpha = 0.3 + S.glowPulse * 0.14;
    ctx.strokeStyle = P.accent;
    ctx.lineWidth = 1.3;
    for (let i = 0; i < B.orbit; i++) {
      ctx.beginPath();
      ctx.ellipse(0, -2, B.rx + 10 + i * 6, B.ry + 6 + i * 4, 0, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawMecha(ctx, spec, compact) {
    const P = spec.palette;
    const B = spec.body;
    const hum = 0.55 + Math.sin(S.tick * 0.08) * 0.45;
    drawMechaBase(ctx, B, P, hum);
    drawMechaArms(ctx, B, P);

    addShadowOval(ctx, 0, 10, B.rx * 0.82, B.ry * 0.58, compact ? 0.08 : 0.1);
    softStroke(ctx, P.line, compact ? 2.6 : 1.95);
    const chassis = ctx.createLinearGradient(-B.rx, -B.ry, B.rx, B.ry + 18);
    chassis.addColorStop(0, '#ffffff');
    chassis.addColorStop(0.2, P.shell);
    chassis.addColorStop(0.58, P.body);
    chassis.addColorStop(1, P.line);
    ctx.fillStyle = chassis;
    roundedRectPath(ctx, -B.rx, -B.ry + 4, B.rx * 2, B.ry * 2 + 6, 24);
    ctx.fill();
    ctx.stroke();

    const panelGrad = ctx.createLinearGradient(-B.rx, -B.ry, B.rx, B.ry);
    panelGrad.addColorStop(0, 'rgba(255,255,255,.96)');
    panelGrad.addColorStop(1, P.shell);
    ctx.fillStyle = panelGrad;
    roundedRectPath(ctx, -B.rx + 6, -B.ry + 10, (B.rx - 6) * 2, (B.ry - 11) * 2, 18);
    ctx.fill();
    addGloss(ctx, 0, -6, B.rx - 6, B.ry - 10);

    if (B.horns) drawMechaHorns(ctx, B, P);
    drawMechaAttachments(ctx, B, P, hum);

    drawMechaScreen(ctx, B, P, hum);
    ctx.globalAlpha = 1;
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(0, -1, B.core + 5, 0, Math.PI * 2);
    ctx.stroke();
    if (B.visor) drawMechaVisor(ctx, B, P);

    drawEye(ctx, -11, -8, P.line, P.accent, compact);
    drawEye(ctx, 11, -8, P.line, P.accent, compact);
    drawMouth(ctx, 0, 10, P.line, compact);
    drawMechaCheeks(ctx, P);
  }

  function drawMechaAttachments(ctx, B, P, hum) {
    if (S.stage === 'servo') {
      ctx.save();
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.moveTo(-10, -B.ry + 12);
      ctx.lineTo(-18, -B.ry + 4);
      ctx.moveTo(10, -B.ry + 12);
      ctx.lineTo(18, -B.ry + 4);
      ctx.stroke();
      ctx.fillStyle = P.accent;
      ctx.globalAlpha = 0.45;
      ctx.beginPath();
      ctx.arc(0, B.ry + 10, 12, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      return;
    }
    if (S.stage === 'forge') {
      ctx.save();
      ctx.fillStyle = P.body;
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.6;
      roundedRectPath(ctx, -B.rx - 5, -6, 10, 26, 5);
      ctx.fill();
      ctx.stroke();
      roundedRectPath(ctx, B.rx - 5, -6, 10, 26, 5);
      ctx.fill();
      ctx.stroke();
      ctx.globalAlpha = 0.26 + hum * 0.16;
      ctx.fillStyle = P.accent;
      ctx.beginPath();
      ctx.moveTo(-12, B.ry + 10);
      ctx.lineTo(0, B.ry + 22);
      ctx.lineTo(12, B.ry + 10);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
      return;
    }
    if (S.stage === 'core') {
      ctx.save();
      ctx.globalAlpha = 0.3 + hum * 0.2;
      ctx.strokeStyle = P.accent;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.ellipse(0, -2, B.rx + 10, B.ry + 8, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(0, -2, B.rx + 16, B.ry + 14, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }

  function drawMechaScreen(ctx, B, P, hum) {
    ctx.save();
    const screen = ctx.createLinearGradient(-18, -24, 18, 12);
    screen.addColorStop(0, 'rgba(255,255,255,.95)');
    screen.addColorStop(0.25, '#bff9ff');
    screen.addColorStop(1, '#7de9f4');
    ctx.fillStyle = screen;
    const inset = S.stage === 'seed' ? 19 : S.stage === 'core' ? 23 : 21;
    const height = S.stage === 'forge' ? 26 : 30;
    roundedRectPath(ctx, -inset, -24, inset * 2, height, S.stage === 'forge' ? 9 : 14);
    ctx.fill();
    ctx.globalAlpha = 0.18 + hum * 0.18;
    ctx.fillStyle = '#ffffff';
    roundedRectPath(ctx, -15, -19, S.stage === 'core' ? 18 : 13, 7, 5);
    ctx.fill();
    ctx.restore();

    ctx.fillStyle = P.accent;
    ctx.globalAlpha = 0.38 + hum * 0.3;
    ctx.beginPath();
    ctx.arc(0, S.stage === 'seed' ? 1 : -1, B.core, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawMechaCheeks(ctx, P) {
    drawBlush(ctx, -17, 17, 1, 0.17);
  }

  function drawMechaArms(ctx, B, P) {
    const punch = S.mood === 'play' ? Math.sin(S.tick * 0.25) * 10 : 0;
    [[-1, -1], [1, 1]].forEach(([dir], idx) => {
      ctx.save();
      const armY = S.stage === 'seed' ? 6 : S.stage === 'core' ? -1 : 2;
      ctx.translate(dir * (B.arms - 4), armY + (idx === 0 ? punch : -punch) * 0.16);
      ctx.rotate(dir * (S.stage === 'core' ? 0.2 : 0.14 + Math.sin(S.tick * 0.08 + idx) * 0.05));
      ctx.strokeStyle = P.line;
      ctx.lineWidth = S.stage === 'core' ? 5.2 : S.stage === 'forge' ? 4.8 : 4.2;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(dir * (S.stage === 'seed' ? 8 : 10), S.stage === 'core' ? 10 : 8);
      ctx.stroke();
      ctx.fillStyle = S.stage === 'forge' ? P.body : P.shell;
      ctx.strokeStyle = P.line;
      ctx.beginPath();
      ctx.ellipse(dir * 13, S.stage === 'core' ? 11 : 10, S.stage === 'seed' ? 5.6 : 6.8, S.stage === 'seed' ? 4.8 : 5.8, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    });
  }

  function drawMechaBase(ctx, B, P, hum) {
    const baseY = B.ry + 2;
    const baseW = B.rx * 1.34;

    ctx.save();
    ctx.globalAlpha = 0.22 + hum * 0.08;
    ctx.fillStyle = P.accent;
    ctx.beginPath();
    ctx.ellipse(0, baseY + 16, baseW * 0.52, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    if (S.stage === 'seed') {
      ctx.fillStyle = P.shell;
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.7;
      roundedRectPath(ctx, -baseW * 0.36, baseY + 3, baseW * 0.72, 10, 6);
      ctx.fill();
      ctx.stroke();
      ctx.save();
      ctx.globalAlpha = 0.3 + hum * 0.1;
      ctx.fillStyle = P.accent;
      ctx.beginPath();
      ctx.moveTo(-7, baseY + 15);
      ctx.lineTo(0, baseY + 24);
      ctx.lineTo(7, baseY + 15);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
      return;
    }

    if (S.stage === 'forge') {
      ctx.fillStyle = P.shell;
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.8;
      roundedRectPath(ctx, -baseW * 0.5, baseY, baseW, 15, 6);
      ctx.fill();
      ctx.stroke();
      roundedRectPath(ctx, -baseW * 0.42, baseY + 3, 14, 9, 4);
      ctx.fill();
      ctx.stroke();
      roundedRectPath(ctx, baseW * 0.28, baseY + 3, 14, 9, 4);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillStyle = P.shell;
      ctx.strokeStyle = P.line;
      ctx.lineWidth = 1.7;
      roundedRectPath(ctx, -baseW * 0.5, baseY, baseW, 12, 6);
      ctx.fill();
      ctx.stroke();
    }

    ctx.save();
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#ffffff';
    roundedRectPath(ctx, -baseW * 0.36, baseY + 2, baseW * 0.28, 4, 2);
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = 0.32 + hum * 0.14;
    ctx.fillStyle = P.accent;
    ctx.beginPath();
    ctx.moveTo(-8, baseY + 18);
    ctx.lineTo(0, baseY + (S.stage === 'core' ? 31 : 28) + Math.sin(S.tick * 0.14) * 2.2);
    ctx.lineTo(8, baseY + 18);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawMechaHorns(ctx, B, P) {
    if (!B.horns) return;
    ctx.fillStyle = S.stage === 'forge' ? P.body : '#eef8ff';
    ctx.strokeStyle = P.line;
    ctx.lineWidth = S.stage === 'core' ? 1.7 : 1.25;
    [[-1], [1]].forEach(([dir]) => {
      ctx.beginPath();
      ctx.moveTo(dir * 14, -B.ry + 14);
      ctx.quadraticCurveTo(dir * (S.stage === 'core' ? 25 : 22), -B.ry + 2, dir * 18, -B.ry + 19);
      ctx.quadraticCurveTo(dir * 14, -B.ry + 20, dir * 12, -B.ry + 16);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }

  function drawMechaVisor(ctx, B, P) {
    ctx.save();
    ctx.globalAlpha = 0.26 + S.glowPulse * 0.18;
    ctx.fillStyle = P.accent;
    roundedRectPath(ctx, -24, S.stage === 'core' ? -22 : -20, 48, S.stage === 'core' ? 16 : 14, 7);
    ctx.fill();
    ctx.restore();
  }

  function drawDiamond(ctx, x, y, size, fill, stroke) {
    ctx.beginPath();
    ctx.moveTo(x, y - size);
    ctx.lineTo(x + size, y);
    ctx.lineTo(x, y + size);
    ctx.lineTo(x - size, y);
    ctx.closePath();
    if (fill) {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
  }

  function roundedRectPath(ctx, x, y, w, h, r) {
    const rr = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  window.PetRenderer = {
    update: updatePet,
    triggerMood,
    addParticles(type, count) {
      addParticles(type || 'heart', count || 4, MAIN_SIZE.width * 0.5, MAIN_SIZE.height * 0.38);
    },
    say: setSpeech,
    renderPreview,
  };

  document.addEventListener('DOMContentLoaded', init);
})();
