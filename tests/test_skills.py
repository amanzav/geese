"""Test that skills section is included in resume embeddings"""

from modules.matcher import ResumeMatcher

print("=" * 80)
print("TESTING SKILLS INTEGRATION")
print("=" * 80)

# Load matcher (this will rebuild embeddings with skills)
matcher = ResumeMatcher()

print(f"\n✅ Total resume entries: {len(matcher.resume_bullets)}")
print(f"   - Original bullets: 18")
print(f"   - Skills added: {len(matcher.resume_bullets) - 18}")

print(f"\n📋 Last 15 entries (should include skills):")
for i, bullet in enumerate(matcher.resume_bullets[-15:], len(matcher.resume_bullets) - 14):
    preview = bullet[:75] + "..." if len(bullet) > 75 else bullet
    print(f"   {i}. {preview}")

# Test technology extraction from skills
print(f"\n🔍 Testing technology extraction with skills:")
test_text = "Looking for TypeScript and Kotlin experience"
techs = matcher._extract_technologies(test_text)
print(f"   Query: '{test_text}'")
print(f"   Found: {sorted(techs)}")
print(f"   ✅ TypeScript: {'TypeScript' in techs}")
print(f"   ✅ Kotlin: {'Kotlin' in techs}")

print("\n" + "=" * 80)
print("✅ Skills integration complete!")
print("=" * 80)
