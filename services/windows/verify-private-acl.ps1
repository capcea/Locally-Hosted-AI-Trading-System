param([Parameter(Mandatory=$true)][string]$Path)
$ErrorActionPreference = 'Stop'
$acl = Get-Acl -LiteralPath $Path
$serviceSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$allowed = @($serviceSid, 'S-1-5-18', 'S-1-5-32-544')
foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
    if ($rule.AccessControlType -eq 'Allow' -and $allowed -notcontains $sid) {
        throw 'Only the service identity, SYSTEM and local administrators may access credentials'
    }
}
exit 0
