local HttpService = game:GetService("HttpService")
local network = require(game:GetService("ReplicatedStorage").Library.Client.Network)

local apiUrl = "https://colourleaderboard.onrender.com/leaderboard?auth=YourAPIKey"

local teamNames = {
    [1] = "Team Blue",
    [2] = "Team Purple",
    [3] = "Team Red",
    [4] = "Team Orange",
    [5] = "Team Yellow",
    [6] = "Team Green"
}

local function formatNumberWithCommas(number)
    local formatted = tostring(number)
    while true do
        formatted, k = string.gsub(formatted, "^(-?%d+)(%d%d%d)", '%1,%2')
        if k == 0 then break end
    end
    return formatted
end

local function formatPoints(points)
    if points >= 1e12 then
        return string.format("%.2ft", points / 1e12)
    elseif points >= 1e9 then
        return string.format("%.2fb", points / 1e9)
    elseif points >= 1e6 then
        return string.format("%.2fm", points / 1e6)
    else
        return tostring(points)
    end
end


local latestTeamInfo = nil
local latestWinningTeam = nil
local canSendEmbed = true

local function updateAPI()
    print("updateAPI called")
    if not latestTeamInfo or not canSendEmbed then return end

    canSendEmbed = false 

    local sortedTeams = {}
    for teamNumber, teamPoints in pairs(latestTeamInfo) do
        table.insert(sortedTeams, {teamNumber = tonumber(teamNumber), teamPoints = tonumber(teamPoints)})
    end

    table.sort(sortedTeams, function(a, b)
        return a.teamPoints > b.teamPoints
    end)

    local formattedTeams = {}
    for rank, team in ipairs(sortedTeams) do
        local teamName = teamNames[team.teamNumber] or "Unknown Team"
        local formattedPoints = formatNumberWithCommas(team.teamPoints)
        local shortFormPoints = formatPoints(team.teamPoints)
local buckets
if rank == 1 then
    buckets = 5
elseif rank == 2 then
    buckets = 4
elseif rank == 3 then
    buckets = 3
elseif rank == 4 then
    buckets = 2
else
    buckets = 1
end
        table.insert(formattedTeams, {
            teamName = teamName,
            teamNumber = team.teamNumber,
            points = team.teamPoints,
            formattedPoints = formattedPoints,
            shortFormPoints = shortFormPoints,
            buckets = buckets
        })
    end

    local winningTeam = formattedTeams[1]

    local jsonPayload = HttpService:JSONEncode({
        leaderboard = formattedTeams,
        winningTeam = {
            teamName = winningTeam.teamName,
            teamNumber = winningTeam.teamNumber
        }
    })

    local success, response = pcall(function()
        return request({
            Url = apiUrl,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json"
            },
            Body = jsonPayload
        })
    end)

    if success then
        print("API updated successfully")
    else
        warn("Failed to update API: ", response)
    end

    canSendEmbed = true
end

network.Fired("Color Contest: Broadcast"):Connect(function(teamInfo, winningTeam)
    latestTeamInfo = teamInfo
    latestWinningTeam = winningTeam
end)

updateAPI()
print("Initial API update called")

while true do
    wait(30)
    updateAPI()
end
