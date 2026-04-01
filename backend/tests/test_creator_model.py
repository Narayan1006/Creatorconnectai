import pytest
from pydantic import ValidationError

from app.models.creator import Creator, CreatorCreate, CreatorUpdate, CreatorPublic


VALID_DATA = {
    "name": "Alice",
    "avatar_url": "https://example.com/avatar.jpg",
    "niche": ["fitness", "wellness"],
    "platform": "instagram",
    "followers": 10000,
    "engagement_rate": 0.05,
    "bio": "Health & wellness creator",
}


# --- Creator (BaseDocument) ---

def test_creator_valid():
    c = Creator(**VALID_DATA)
    assert c.name == "Alice"
    assert c.followers == 10000
    assert c.engagement_rate == 0.05
    assert c.niche == ["fitness", "wellness"]
    assert c.embedding is None
    assert c.portfolio_url is None


def test_creator_engagement_rate_zero_and_one_are_valid():
    Creator(**{**VALID_DATA, "engagement_rate": 0.0})
    Creator(**{**VALID_DATA, "engagement_rate": 1.0})


def test_creator_engagement_rate_above_one_invalid():
    with pytest.raises(ValidationError, match="engagement_rate"):
        Creator(**{**VALID_DATA, "engagement_rate": 1.01})


def test_creator_engagement_rate_below_zero_invalid():
    with pytest.raises(ValidationError, match="engagement_rate"):
        Creator(**{**VALID_DATA, "engagement_rate": -0.01})


def test_creator_followers_zero_invalid():
    with pytest.raises(ValidationError, match="followers"):
        Creator(**{**VALID_DATA, "followers": 0})


def test_creator_followers_negative_invalid():
    with pytest.raises(ValidationError, match="followers"):
        Creator(**{**VALID_DATA, "followers": -1})


def test_creator_niche_empty_invalid():
    with pytest.raises(ValidationError, match="niche"):
        Creator(**{**VALID_DATA, "niche": []})


# --- CreatorCreate ---

def test_creator_create_valid():
    cc = CreatorCreate(**VALID_DATA)
    assert cc.name == "Alice"


def test_creator_create_invalid_engagement_rate():
    with pytest.raises(ValidationError, match="engagement_rate"):
        CreatorCreate(**{**VALID_DATA, "engagement_rate": 2.0})


def test_creator_create_invalid_followers():
    with pytest.raises(ValidationError, match="followers"):
        CreatorCreate(**{**VALID_DATA, "followers": 0})


def test_creator_create_invalid_niche():
    with pytest.raises(ValidationError, match="niche"):
        CreatorCreate(**{**VALID_DATA, "niche": []})


# --- CreatorUpdate ---

def test_creator_update_all_none_is_valid():
    cu = CreatorUpdate()
    assert cu.name is None
    assert cu.followers is None


def test_creator_update_partial_valid():
    cu = CreatorUpdate(followers=500, engagement_rate=0.1)
    assert cu.followers == 500
    assert cu.engagement_rate == 0.1


def test_creator_update_invalid_engagement_rate():
    with pytest.raises(ValidationError, match="engagement_rate"):
        CreatorUpdate(engagement_rate=1.5)


def test_creator_update_invalid_followers():
    with pytest.raises(ValidationError, match="followers"):
        CreatorUpdate(followers=-10)


def test_creator_update_empty_niche_invalid():
    with pytest.raises(ValidationError, match="niche"):
        CreatorUpdate(niche=[])


# --- CreatorPublic ---

def test_creator_public_excludes_embedding():
    c = Creator(**{**VALID_DATA, "embedding": [0.1, 0.2, 0.3]})
    pub = CreatorPublic(**c.model_dump(by_alias=True))
    assert not hasattr(pub, "embedding") or "embedding" not in pub.model_fields
    # Ensure embedding is not in the serialized output
    assert "embedding" not in pub.model_dump()


def test_creator_public_has_expected_fields():
    c = Creator(**VALID_DATA)
    pub = CreatorPublic(**c.model_dump(by_alias=True))
    data = pub.model_dump()
    for field in ("name", "avatar_url", "niche", "platform", "followers", "engagement_rate", "bio"):
        assert field in data
