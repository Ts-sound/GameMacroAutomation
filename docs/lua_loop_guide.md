# Lua 循环控制使用指南

## API 概览

### 1. `loop_while(condition, body, max_iterations, interval)`

当条件为 true 时持续循环。

**参数:**
- `condition` (function): 条件函数，返回 true 继续循环
- `body` (function): 循环体函数
- `max_iterations` (int): 最大循环次数（防止无限循环）
- `interval` (int): 每次循环间隔毫秒

**示例:**
```lua
-- 当 Boss 血条存在时持续攻击
loop_while(
    function()
        return image_exists("boss_hp_bar", 0.7)
    end,
    function()
        click_image("attack_btn")
        delay(1000)
    end,
    100,    -- 最多循环 100 次
    1000    -- 每次间隔 1 秒
)
```

### 2. `loop_times(count, body, delay_ms)`

固定次数循环。

**参数:**
- `count` (int): 循环次数
- `body` (function): 循环体函数
- `delay_ms` (int): 每次循环间隔毫秒

**示例:**
```lua
-- 拾取 5 次物品
loop_times(
    5,
    function()
        click_image("item_1")
        delay(500)
    end,
    200  -- 每次间隔 200ms
)
```

### 3. `loop_until(condition, body, timeout, interval)`

直到条件满足才停止的循环。

**参数:**
- `condition` (function): 停止条件函数，返回 true 停止循环
- `body` (function): 循环体函数
- `timeout` (int): 超时时间（毫秒）
- `interval` (int): 每次循环间隔毫秒

**示例:**
```lua
-- 直到奖励弹窗出现
loop_until(
    function()
        return image_exists("reward_popup", 0.8)
    end,
    function()
        click_image("collect_btn")
        delay(1000)
    end,
    30000,  -- 30 秒超时
    2000    -- 每 2 秒检查一次
)
```

## 完整示例

### 战斗流程

```lua
function main()
    log("=== 战斗开始 ===", "INFO")
    
    -- 1. 等待 Boss 出现
    if not wait_image("boss_hp_bar", 10000) then
        log("Boss 未出现", "ERROR")
        return false
    end
    
    -- 2. 战斗循环：Boss 血条存在时持续攻击
    loop_while(
        function()
            return image_exists("boss_hp_bar", 0.7)
        end,
        function()
            -- 检查血量
            if image_exists("low_hp_warning", 0.8) then
                run_script("potion.yaml")
            else
                click_image("skill_1")
            end
            delay(1000)
        end,
        100,    -- 最大 100 次
        1000    -- 间隔 1 秒
    )
    
    -- 3. 拾取物品（固定 5 次）
    loop_times(
        5,
        function()
            click_image("item_1")
            delay(300)
        end,
        200
    )
    
    -- 4. 等待奖励弹窗
    loop_until(
        function()
            return image_exists("reward_popup", 0.8)
        end,
        function()
            click_image("collect_btn")
            delay(1000)
        end,
        30000,  -- 30 秒超时
        2000
    )
    
    log("=== 战斗结束 ===", "INFO")
    return true
end
```

### 副本循环

```lua
function main()
    local dungeon_count = 0
    local max_dungeons = 10
    
    -- 循环刷副本
    loop_times(
        max_dungeons,
        function()
            dungeon_count = dungeon_count + 1
            log("第 " .. dungeon_count .. " 次副本", "INFO")
            
            -- 进入副本
            click_image("enter_btn")
            delay(2000)
            
            -- 等待进入战斗
            loop_until(
                function()
                    return image_exists("boss_hp_bar", 0.7)
                end,
                function()
                    click_image("start_btn")
                    delay(1000)
                end,
                30000,
                1000
            )
            
            -- 战斗循环
            loop_while(
                function()
                    return image_exists("boss_hp_bar", 0.7)
                end,
                function()
                    if image_exists("low_hp_warning", 0.8) then
                        run_script("potion.yaml")
                    else
                        click_image("attack_btn")
                    end
                    delay(1000)
                end,
                100,
                1000
            )
            
            -- 领取奖励
            if wait_image("reward_popup", 5000) then
                click_image("reward_popup")
                delay(1000)
            end
            
            -- 退出副本
            click_image("exit_btn")
            delay(2000)
        end,
        3000  -- 每个副本间隔 3 秒
    )
    
    log("副本完成，共 " .. dungeon_count .. " 次", "INFO")
end
```

## 使用技巧

### 1. 组合使用循环

```lua
-- 外层：固定次数（刷 10 次副本）
loop_times(10, function()
    -- 内层：条件循环（Boss 存在时攻击）
    loop_while(
        function() return image_exists("boss_hp") end,
        function() click_image("attack") delay(1000) end,
        100, 1000
    )
    
    -- 内层：直到条件满足（直到奖励出现）
    loop_until(
        function() return image_exists("reward") end,
        function() click_image("collect") delay(1000) end,
        30000, 2000
    )
end, 5000)
```

### 2. 使用变量计数

```lua
local special_attack_count = 0

loop_while(
    function() return image_exists("enemy") end,
    function()
        special_attack_count = special_attack_count + 1
        
        -- 每 5 次普通攻击后使用大招
        if special_attack_count % 5 == 0 then
            click_image("ultimate_skill")
        else
            click_image("normal_attack")
        end
        
        delay(1000)
    end,
    100, 1000
)
```

### 3. 条件判断 + 循环

```lua
-- 先检查是否需要补给
if image_exists("low_potion", 0.8) then
    log("药水不足，先购买药水", "INFO")
    run_script("buy_potion.yaml")
end

-- 然后开始战斗
loop_while(
    function() return image_exists("enemy") end,
    function()
        -- 战斗中持续检查血量
        if image_exists("low_hp", 0.8) then
            run_script("use_potion.yaml")
        else
            click_image("attack")
        end
        delay(1000)
    end,
    100, 1000
)
```

## 注意事项

1. **始终设置最大循环次数** - 防止死循环
2. **合理设置超时时间** - 避免无限等待
3. **使用日志记录进度** - 方便调试
4. **循环间隔不要太短** - 给游戏反应时间（建议≥500ms）
