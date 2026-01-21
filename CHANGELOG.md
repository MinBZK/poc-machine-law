# CHANGELOG

<!-- version list -->

## v1.6.1 (2026-01-21)

### Bug Fixes

- Unwrap double-wrapped arrays for array type fields
  ([#344](https://github.com/MinBZK/poc-machine-law/pull/344),
  [`1c176c6`](https://github.com/MinBZK/poc-machine-law/commit/1c176c642c3380ac66ddfc3232ccbc6b4c0c0419))

### Chores

- Sync VERSION file to 1.6.0
  ([`58f4a9a`](https://github.com/MinBZK/poc-machine-law/commit/58f4a9aee2d22b6e233df222173fc69871979122))


## v1.6.0 (2026-01-21)

### Bug Fixes

- Deduplicate SELF delegations in get_delegations_for_user
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

- Merge SELF delegation permissions using intersection
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

- Merge static profile properties with dynamic ones
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

- Skip handelingsonbekwaamheid tests in Go engine
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

### Chores

- Sync VERSION file to 1.5.0
  ([`e992cce`](https://github.com/MinBZK/poc-machine-law/commit/e992cce67a631b8bacc0e08cd3c61e45bce0f3d7))

- Update regelrecht-laws submodule to latest main
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

### Features

- Add 8 Dutch delegation law feature files with test scenarios
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

- Add badges for ouderlijk gezag, ondernemer, and minderjarig profiles
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))

- Add extended business delegation tests and handelingsonbekwaamheid
  ([#343](https://github.com/MinBZK/poc-machine-law/pull/343),
  [`5772de4`](https://github.com/MinBZK/poc-machine-law/commit/5772de4f4ac56e027843f6e1fe903bb3baeee2a6))


## v1.5.0 (2026-01-21)

### Bug Fixes

- Admin law toggles now show disabled laws and all law types
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Use inline expanding submenus for demo law toggles
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

### Chores

- Hide nav menu in demo mode, rename Admin beheer to Admin
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Hide proof of concept banner in demo mode
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Remove law toggles from demo workspace
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Sync VERSION file to 1.4.0
  ([`d29c886`](https://github.com/MinBZK/poc-machine-law/commit/d29c886c89f08ac2fedcaadfe4c9ea83f6f2565e))

- Trigger CI rerun ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

### Features

- Add Admin menu item with temporary dismissable tab
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Add compact law toggles to demo menu ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

### Refactoring

- Remove duplicate code in law toggles template
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Side-panel drawer for demo law toggles
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Use drawer menu style for demo law toggles
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))

- Use filter_disabled param instead of separate method
  ([#341](https://github.com/MinBZK/poc-machine-law/pull/341),
  [`da916ae`](https://github.com/MinBZK/poc-machine-law/commit/da916aec28f79a9977ca4cef4303a429e9044663))


## v1.4.0 (2026-01-20)

### Chores

- Sync VERSION file to 1.3.0
  ([`07de281`](https://github.com/MinBZK/poc-machine-law/commit/07de281fa4560b47987fb40355ee62128dac259b))

### Features

- Increase huurtoeslag profile income for better demo
  ([#340](https://github.com/MinBZK/poc-machine-law/pull/340),
  [`6ecf3f9`](https://github.com/MinBZK/poc-machine-law/commit/6ecf3f9dd96bcbe50754e54e3b94f170060eabab))


## v1.3.0 (2026-01-20)

### Bug Fixes

- Ensure menu button appears above PoC ribbon
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

- Format feature_flags partial and disable chat by default
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

- Hide kebab menu in zaaksysteem when in demo mode
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

- Remove PoC ribbon from demo mode due to z-index issues
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

### Chores

- Sync VERSION file to 1.2.0
  ([`225d7db`](https://github.com/MinBZK/poc-machine-law/commit/225d7db019c75795f047af1fc1f69982df2c7955))

### Features

- Add demo mode with PoC ribbon and hidden menus
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

- Add VERSION and feature flags to demo menu
  ([#339](https://github.com/MinBZK/poc-machine-law/pull/339),
  [`05bef74`](https://github.com/MinBZK/poc-machine-law/commit/05bef74e5659ff103bc33e8cb22337f220d9afa0))

### Testing

- Add Archiefwet 1995 BDD tests and step definitions
  ([#220](https://github.com/MinBZK/poc-machine-law/pull/220),
  [`b98e67a`](https://github.com/MinBZK/poc-machine-law/commit/b98e67ac5fbfbe4111f3a53dbedd63fa6e111f7d))

- Add BDD tests for ACICT and AWB Article 1:1 laws
  ([#208](https://github.com/MinBZK/poc-machine-law/pull/208),
  [`7e38395`](https://github.com/MinBZK/poc-machine-law/commit/7e383957e2adf162120b46428879e5ff6e9c51a7))


## v1.2.0 (2026-01-20)

### Bug Fixes

- Update kernenergiewet feature tests to pass all parameters directly
  ([#212](https://github.com/MinBZK/poc-machine-law/pull/212),
  [`bcbf50b`](https://github.com/MinBZK/poc-machine-law/commit/bcbf50bae1db671ea5df734def7d1b4b63730c5f))

### Chores

- Sync VERSION file to 1.1.2
  ([`54bd240`](https://github.com/MinBZK/poc-machine-law/commit/54bd2403adea4a5abbcef51df404f90ce4ffcd37))

- Update regelrecht-laws submodule ([#212](https://github.com/MinBZK/poc-machine-law/pull/212),
  [`bcbf50b`](https://github.com/MinBZK/poc-machine-law/commit/bcbf50bae1db671ea5df734def7d1b4b63730c5f))

- **deps-dev**: Bump the npm-minor-patch group
  ([#338](https://github.com/MinBZK/poc-machine-law/pull/338),
  [`4aaed6b`](https://github.com/MinBZK/poc-machine-law/commit/4aaed6bbafdeee1a57e5381792da088ea01022a8))

- **deps-dev**: Bump the npm-minor-patch group
  ([#337](https://github.com/MinBZK/poc-machine-law/pull/337),
  [`872e840`](https://github.com/MinBZK/poc-machine-law/commit/872e8401115dbed5249506beef59ddd5f8fcdeea))

- **deps-dev**: Bump the npm-minor-patch group
  ([#336](https://github.com/MinBZK/poc-machine-law/pull/336),
  [`4f96357`](https://github.com/MinBZK/poc-machine-law/commit/4f9635713442372d5cd12dbc9a62ce035e559196))

### Documentation

- Add RFC process and rules language selection RFC
  ([`7463233`](https://github.com/MinBZK/poc-machine-law/commit/74632338802cf8c61f68e6f36de7a03103c905ea))

### Features

- Add Kernenergiewet test scenarios and generic step definitions
  ([#212](https://github.com/MinBZK/poc-machine-law/pull/212),
  [`bcbf50b`](https://github.com/MinBZK/poc-machine-law/commit/bcbf50bae1db671ea5df734def7d1b4b63730c5f))


## v1.1.2 (2026-01-20)

### Bug Fixes

- Show objection/appeal options for rejected cases regardless of requirements_met
  ([#89](https://github.com/MinBZK/poc-machine-law/pull/89),
  [`9b6b9b7`](https://github.com/MinBZK/poc-machine-law/commit/9b6b9b76b35780f7932e452e611a63f5a93ad444))

### Chores

- Configure pre-commit.ci to use conventional commits
  ([#334](https://github.com/MinBZK/poc-machine-law/pull/334),
  [`b498c4d`](https://github.com/MinBZK/poc-machine-law/commit/b498c4dda488e14001dff00b2784bcdb281467fd))

- Pre-commit autoupdate ([#335](https://github.com/MinBZK/poc-machine-law/pull/335),
  [`42edb9b`](https://github.com/MinBZK/poc-machine-law/commit/42edb9b667c31b8de24a7eab3b6faf99cfb26fba))

- Sync VERSION file to 1.1.1
  ([`528238d`](https://github.com/MinBZK/poc-machine-law/commit/528238d6a06e6ec9943e794efe1af6f42ea100d5))


## v1.1.1 (2026-01-20)

### Bug Fixes

- Update regelrecht-laws submodule with huurtoeslag fix
  ([#333](https://github.com/MinBZK/poc-machine-law/pull/333),
  [`f2525fa`](https://github.com/MinBZK/poc-machine-law/commit/f2525fac43cb5d4f22d5b9e882949d0720f35390))

### Chores

- Sync VERSION file to 1.1.0
  ([`e66e2e7`](https://github.com/MinBZK/poc-machine-law/commit/e66e2e79cb8c96bc358224cd947632eb9bf01393))


## v1.1.0 (2026-01-19)

### Chores

- Sync VERSION file to 1.0.5
  ([`7d80754`](https://github.com/MinBZK/poc-machine-law/commit/7d80754307bddc30819a1ad5231803799c1fe6d2))

### Features

- Profile properties ([#278](https://github.com/MinBZK/poc-machine-law/pull/278),
  [`47e554b`](https://github.com/MinBZK/poc-machine-law/commit/47e554ba4188b7799c49387809dcba6aa4d40611))


## v1.0.5 (2026-01-19)

### Bug Fixes

- Remove link to claim details, since it results in an error
  ([#309](https://github.com/MinBZK/poc-machine-law/pull/309),
  [`4742a33`](https://github.com/MinBZK/poc-machine-law/commit/4742a33dd4eea8d783dec6249870969134806859))

### Chores

- Sync VERSION file to 1.0.4
  ([`afd38c3`](https://github.com/MinBZK/poc-machine-law/commit/afd38c3d876cfd3e079312fbab4d8b82dcf65a69))


## v1.0.4 (2026-01-19)

### Bug Fixes

- Make nest_asyncio lazy to support uvicorn 0.40.0
  ([#331](https://github.com/MinBZK/poc-machine-law/pull/331),
  [`df5280b`](https://github.com/MinBZK/poc-machine-law/commit/df5280bd22728aef15e8860a634d329e4af695fb))

### Chores

- Sync VERSION file to 1.0.3
  ([`d5754f6`](https://github.com/MinBZK/poc-machine-law/commit/d5754f61552bd8009bf5eab36e3212c08fd34dbe))


## v1.0.3 (2026-01-19)

### Bug Fixes

- Update dependencies to address security vulnerabilities
  ([#330](https://github.com/MinBZK/poc-machine-law/pull/330),
  [`bea80ee`](https://github.com/MinBZK/poc-machine-law/commit/bea80ee23a5c0091b19333599251d4850a43836d))

### Chores

- Sync VERSION file to 1.0.2
  ([`6b35d3d`](https://github.com/MinBZK/poc-machine-law/commit/6b35d3d92f1fe160f852b16f50d8719f15a2c262))


## v1.0.2 (2026-01-19)

### Bug Fixes

- Add missing claimant to edit form template context
  ([#329](https://github.com/MinBZK/poc-machine-law/pull/329),
  [`dd53364`](https://github.com/MinBZK/poc-machine-law/commit/dd533644aa4dbed77bbb1a4eff07248ac114921b))

### Chores

- Ignore behave updates in dependabot (1.3.x breaks tests)
  ([#327](https://github.com/MinBZK/poc-machine-law/pull/327),
  [`e70d7d5`](https://github.com/MinBZK/poc-machine-law/commit/e70d7d54c06ecc653ccf08df60db998a22fed26e))

- Sync VERSION file to 1.0.1
  ([`f21e221`](https://github.com/MinBZK/poc-machine-law/commit/f21e2213f680476af928dcd7a87ebf0b94688ec8))

- Update copyright year to 2026 ([#325](https://github.com/MinBZK/poc-machine-law/pull/325),
  [`31fa65d`](https://github.com/MinBZK/poc-machine-law/commit/31fa65d01465ecda5192bd47e82b9687b6efff7e))

- **deps**: Bump github.com/cucumber/godog
  ([#318](https://github.com/MinBZK/poc-machine-law/pull/318),
  [`0fe2298`](https://github.com/MinBZK/poc-machine-law/commit/0fe22985b1bed1e03d9f4c654a070d1d9f851f4d))

- **deps**: Bump the actions group across 1 directory with 3 updates
  ([#326](https://github.com/MinBZK/poc-machine-law/pull/326),
  [`4b3c964`](https://github.com/MinBZK/poc-machine-law/commit/4b3c964473b096f6cd4c391dc1e3093a888ccfc1))


## v1.0.1 (2026-01-19)

### Bug Fixes

- Sync VERSION file and simplify workflow
  ([#324](https://github.com/MinBZK/poc-machine-law/pull/324),
  [`d4d78c7`](https://github.com/MinBZK/poc-machine-law/commit/d4d78c72d892fbe28b35a68284d72001d817facd))


## v1.0.0 (2026-01-19)

- Initial Release
