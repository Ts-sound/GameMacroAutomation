-- 战斗循环示例
-- 使用 Lua 控制条件循环执行

function main()
    log("=== 战斗循环开始 ===", "INFO")
    
    -- 等待战斗开始（Boss 血条出现）
    log("等待 Boss 出现...", "INFO")
    if not wait_image("boss_hp_bar", 10000) then
        log("Boss 未出现，退出", "ERROR")
        return false
    end
    
    -- 循环 1: 使用 loop_while - 当 Boss 血条存在时继续攻击
    local max_iterations = 100
    local attack_count = 0
    
    log("开始战斗循环...", "INFO")
    loop_while(
        function()
            -- 循环条件：Boss 血条存在
            return image_exists("boss_hp_bar", 0.7)
        end,
        function()
            -- 循环体：执行攻击动作
            attack_count = attack_count + 1
            log("第 " .. attack_count .. " 次攻击", "INFO")
            
            -- 检查是否需要喝药水
            if image_exists("low_hp_warning", 0.8) then
                log("血量低，喝药水", "WARNING")
                run_script("potion.yaml")
            else
                -- 普通攻击
                click_image("attack_btn", 0.8)
            end
            
            -- 技能冷却延迟
            delay(1000)
        end,
        max_iterations,  ---- 最大循环次数
        1000             -- 每次循环间隔 (ms)
    )
    
    log("战斗结束，攻击次数：" .. attack_count, "INFO")
    
    -- 循环 2: 使用 loop_times - 固定次数拾取物品
    log("拾取物品...", "INFO")
    loop_times(
        5,  -- 拾取 5 次
        function()
            click_image("item_1", 0.8)
            delay(500)
        end,
        200  -- 每次间隔 200ms
    )
    
    -- 循环 3: 使用 loop_until - 直到奖励弹窗出现
    log("等待奖励弹窗...", "INFO")
    local reward_received = false
    loop_until(
        function()
            -- 停止条件：奖励弹窗存在
            return image_exists("reward_popup", 0.8)
        end,
        function()
            -- 循环体：点击收集按钮
            log("点击收集按钮...", "DEBUG")
            click_image("collect_btn", 0.8)
            delay(1000)
        end,
        30000,  -- 超时 30 秒
        2000    -- 每 2 秒检查一次
    )
    
    -- 领取奖励
    if image_exists("reward_popup", 0.8) then
        log("领取奖励", "INFO")
        click_image("reward_popup", 0.9)
        delay(500)
    end
    
    log("=== 战斗循环结束 ===", "INFO")
    return true
end
