Feature: SBS login
  Scenario Outline: Verifying SBS login user <user>
     Given SBS health UP
       and we visit profile
       and we choose SRAM Monitoring IdP
      When we login as <user>
      Then <user> name in profile

  Examples: Test
        | user     |
        | student  |
        | employee |
