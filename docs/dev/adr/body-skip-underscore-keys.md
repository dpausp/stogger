# body-skip-underscore-keys

## Context

The console/file renderer renders underscore-prefixed event_dict keys twice when no `_replace_msg` is provided: once as generic key=value pairs in the fallback body, and again in the dedicated output-section stage that consumes them. The same keys are also exposed to `_replace_msg` format-string interpolation, allowing internal fields to leak into user-controlled message templates. This violates the [structlog convention](https://www.structlog.org/en/stable/contents.html) where the `_` prefix marks internal keys that are consumed by render stages and must not appear in user-facing output.

## Decisions

### underscore-keys-excluded-from-body

#### Context

Underscore-prefixed keys in event_dict represent internal or special fields handled by dedicated render stages (e.g. the output-section stage). Without `_replace_msg`, these keys leak into the generic KV body rendering and appear duplicated in the rendered output — once in the body, once via their dedicated stage.

#### Decision

The fallback KV body renderer MUST skip all event_dict keys whose name starts with `_`. The dedicated render stages that consume these keys remain unchanged.

#### Alternatives

a. Hardcoded list of known internal keys — fragile, breaks on any future internal key added, and does not match the structlog `_`-prefix convention.
b. Pop the output keys earlier in the internal-field stripping stage — wrong, because they must remain in event_dict for the dedicated output-section stage to consume.

#### Consequences

All underscore-prefixed keys are excluded from the fallback body. A caller passing a custom `_foo` key without `_replace_msg` will see that key silently dropped from the body. This matches the structlog convention and is the intended behaviour. Tests must verify (1) no duplication of output keys in rendered output, and (2) no underscore-prefixed key appears in the fallback body.

### underscore-keys-excluded-from-replace-msg-interpolation

#### Context

The replace-message formatter receives the full event_dict as keyword arguments, which exposes underscore-prefixed internal keys for unintended interpolation (e.g. referencing the raw output key from a user format string).

#### Decision

When building the keyword arguments for the replace-message formatter, keys whose name starts with `_` MUST be excluded.

#### Alternatives

a. Exclude only `_replace_msg` itself — leaves all other internal keys exposed to user-controlled format strings.
b. No filtering, document as a feature — violates least-surprise; internal fields should not be reachable from user format strings.

#### Consequences

Underscore-prefixed keys cannot be referenced from `_replace_msg` format strings. This is desirable: internal fields are rendered via their dedicated stages, not via message interpolation.

## Verified By
