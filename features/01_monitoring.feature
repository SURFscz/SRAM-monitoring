Feature: Monitoring
  Scenario Outline: Verifying End-to-End flow for user <user>
     Given SBS health UP
       and we visit monitoring <start>
       and we choose SRAM Monitoring IdP
      When we login as <user>
      Then test userdata for <user> in <start>

  Examples: Test
        | start      | user      |
        | oidc_url   | student   |
        | saml_url   | student   |
        | oidc_url   | employee  |
        | saml_url   | employee  |
