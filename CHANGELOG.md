# Changelog

<!--next-version-placeholder-->

## v1.2.2 (2026-02-17)
### Fix
* Treat HttpStatus.UNKNOWN as retryable ([#70](https://github.com/amplitude/Amplitude-Python/issues/70)) ([`3e1db08`](https://github.com/amplitude/Amplitude-Python/commit/3e1db08f110c570a7d7c07692e121703e8d376e0))

## v1.2.1 (2025-11-19)
### Fix
* Respect flush_queue_size in Worker.flush() ([#64](https://github.com/amplitude/Amplitude-Python/issues/64)) ([`d9accf0`](https://github.com/amplitude/Amplitude-Python/commit/d9accf06bafa27446a641cc84a5d8a3f8a86c700))

## v1.2.0 (2025-07-01)
### Feature
* Add support for setting user agent on event ([#61](https://github.com/amplitude/Amplitude-Python/issues/61)) ([`bda8b95`](https://github.com/amplitude/Amplitude-Python/commit/bda8b95f50daf092f0fe570fab473e2255f6f5d5))

## v1.1.5 (2025-02-26)
### Fix
* Adding currency property to events ([#60](https://github.com/amplitude/Amplitude-Python/issues/60)) ([`6984e76`](https://github.com/amplitude/Amplitude-Python/commit/6984e769d486048f73c08f7003862c16876b3d99))

## v1.1.4 (2023-12-12)
### Fix
* Allow none property value but not send ([#54](https://github.com/amplitude/Amplitude-Python/issues/54)) ([`677ebe7`](https://github.com/amplitude/Amplitude-Python/commit/677ebe72efe86f231bd4c4bfc13f02794ff63b8b))

## v1.1.3 (2023-09-01)
### Fix
* Set group should set user property ([#51](https://github.com/amplitude/Amplitude-Python/issues/51)) ([`964a1b6`](https://github.com/amplitude/Amplitude-Python/commit/964a1b6693a98f4343e9b4c9f94f89a1b747335c))

## v1.1.2 (2023-08-04)
### Fix
* Mutable defaults in init ([#48](https://github.com/amplitude/Amplitude-Python/issues/48)) ([`958e394`](https://github.com/amplitude/Amplitude-Python/commit/958e394242e1b0bd9b988a782e611254e496d6e6))

## v1.1.1 (2023-01-11)
### Fix
* Try fix script cleanup ([#43](https://github.com/amplitude/Amplitude-Python/issues/43)) ([`8c2f0b7`](https://github.com/amplitude/Amplitude-Python/commit/8c2f0b7c1b3f9bdf321b8ca0c1ac6ed5f62e5865))

## v1.1.0 (2022-09-08)
### Feature
* Add ingestion_metadata field ([#36](https://github.com/amplitude/Amplitude-Python/issues/36)) ([`a74a943`](https://github.com/amplitude/Amplitude-Python/commit/a74a943caab46e51a63c2933ce680aa9a345e7d9))
* Add library context identifier ([#33](https://github.com/amplitude/Amplitude-Python/issues/33)) ([`d1c8f52`](https://github.com/amplitude/Amplitude-Python/commit/d1c8f52c595361d59cb9f0cfaa3cb13afb75ee30))
* Add version_name to EventOptions ([#31](https://github.com/amplitude/Amplitude-Python/issues/31)) ([`5f9f098`](https://github.com/amplitude/Amplitude-Python/commit/5f9f098f08cd5293ceb896e17435fc5249129adf))

### Fix
* Update pyproject to use tag version to fix release workflow ([#37](https://github.com/amplitude/Amplitude-Python/issues/37)) ([`885fd5b`](https://github.com/amplitude/Amplitude-Python/commit/885fd5bc13d97ba1098ae175321409a440eadd23))

### Documentation
* Update Ampli Python url ([#34](https://github.com/amplitude/Amplitude-Python/issues/34)) ([`45d2a67`](https://github.com/amplitude/Amplitude-Python/commit/45d2a67ecb588a82f807686ace02c24be04c6bd2))

## v0.4.1 (2022-06-23)
### Fix
* Get_event_body for enum value from ampli ([#29](https://github.com/amplitude/Amplitude-Python/issues/29)) ([`2bbc1b0`](https://github.com/amplitude/Amplitude-Python/commit/2bbc1b093d800641f846a02194fd3adb7d3bb31d))
* Set_group put group_type/group_name in groups attribute ([#28](https://github.com/amplitude/Amplitude-Python/issues/28)) ([`828040e`](https://github.com/amplitude/Amplitude-Python/commit/828040e08e2ecc7b3ff240cc25dd58fba573e12a))
* Add process logs & flush() returns future ([#27](https://github.com/amplitude/Amplitude-Python/issues/27)) ([`33d4c5c`](https://github.com/amplitude/Amplitude-Python/commit/33d4c5c08a8fb00af177e86f50db10af5dc239b6))

## v0.4.0 (2022-06-03)
### Feature
* Add plan to config ([#26](https://github.com/amplitude/Amplitude-Python/issues/26)) ([`eb3edf9`](https://github.com/amplitude/Amplitude-Python/commit/eb3edf969a29e372da054fb44d2ea8cc89b09d42))

## v0.3.0 (2022-05-12)
### Feature
* Flask and django simple example ([#22](https://github.com/amplitude/Amplitude-Python/issues/22)) ([`c71b8e0`](https://github.com/amplitude/Amplitude-Python/commit/c71b8e0de36eafaa3af673af8ef35e4485107137))

### Fix
* Set correct fetch-depth for semantic release ([#25](https://github.com/amplitude/Amplitude-Python/issues/25)) ([`0514d40`](https://github.com/amplitude/Amplitude-Python/commit/0514d40665a1d52bec999301eeca609c28a9e9d6))
* Broken release action ([#24](https://github.com/amplitude/Amplitude-Python/issues/24)) ([`8eb6e52`](https://github.com/amplitude/Amplitude-Python/commit/8eb6e5242d77a84d6516dce96e8b8411e6fc1247))

## v0.2.2 (2022-04-29)
### Fix
* Use new thread instead of background blocking thread ([#20](https://github.com/amplitude/Amplitude-Python/issues/20)) ([`24f807f`](https://github.com/amplitude/Amplitude-Python/commit/24f807f3c9eb2806deb83c5545151ca034e3ce20))

## v0.2.1 (2022-04-21)
### Fix
* Handles exceptions raised by `request.urlopen` in `HttpClient.post` ([#17](https://github.com/amplitude/Amplitude-Python/issues/17)) ([`4150ea0`](https://github.com/amplitude/Amplitude-Python/commit/4150ea000bb9c67f630c99df4bdf40b8f6fde568))

## v0.2.0 (2022-04-16)
### Feature
* Unit test for client module ([#15](https://github.com/amplitude/Amplitude-Python/issues/15)) ([`0cdb0b4`](https://github.com/amplitude/Amplitude-Python/commit/0cdb0b46bcde7b974791d10f0d4ff42c842fe42b))
