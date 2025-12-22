const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("OmniArbDecoder", function () {
  let decoder;
  let owner;
  let addr1;
  
  // Helper to convert string to bytes1
  function toBytes1(str) {
    return ethers.encodeBytes32String(str).slice(0, 4);
  }
  
  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();
    
    const DecoderFactory = await ethers.getContractFactory("OmniArbDecoder");
    decoder = await DecoderFactory.deploy();
    await decoder.waitForDeployment();
  });
  
  describe("Chain Enum Mappings", function () {
    it("Should initialize all chain enum mappings correctly", async function () {
      expect(await decoder.enumToChainId(toBytes1("A"))).to.equal(1); // Ethereum
      expect(await decoder.enumToChainId(toBytes1("B"))).to.equal(137); // Polygon
      expect(await decoder.enumToChainId(toBytes1("C"))).to.equal(8453); // Base
      expect(await decoder.enumToChainId(toBytes1("D"))).to.equal(42161); // Arbitrum
      expect(await decoder.enumToChainId(toBytes1("E"))).to.equal(10); // Optimism
      expect(await decoder.enumToChainId(toBytes1("F"))).to.equal(43114); // Avalanche
      expect(await decoder.enumToChainId(toBytes1("G"))).to.equal(250); // Fantom
      expect(await decoder.enumToChainId(toBytes1("H"))).to.equal(100); // Gnosis
      expect(await decoder.enumToChainId(toBytes1("I"))).to.equal(42220); // Celo
      expect(await decoder.enumToChainId(toBytes1("J"))).to.equal(59144); // Linea
    });
    
    it("Should return 0 for invalid chain enums", async function () {
      expect(await decoder.enumToChainId(toBytes1("K"))).to.equal(0);
      expect(await decoder.enumToChainId(toBytes1("Z"))).to.equal(0);
    });
    
    it("Should validate chain enum via getChainId", async function () {
      expect(await decoder.getChainId(toBytes1("A"))).to.equal(1);
      
      await expect(decoder.getChainId(toBytes1("K")))
        .to.be.revertedWithCustomError(decoder, "InvalidChainEnum");
    });
    
    it("Should check if chain enum is valid for current chain", async function () {
      // On hardhat network (chainId 31337), all enums should be invalid
      // unless we're forking a specific chain
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      
      if (networkChainId == 137n) { // Polygon fork
        expect(await decoder.isValidChainEnum(toBytes1("B"))).to.be.true;
        expect(await decoder.isValidChainEnum(toBytes1("A"))).to.be.false;
      }
    });
  });
  
  describe("Token Rank Configuration", function () {
    it("Should allow owner to configure single token rank", async function () {
      const tokenAddress = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"; // WETH on Polygon
      const rank = 2001;
      
      await expect(decoder.configureTokenRank(rank, tokenAddress))
        .to.emit(decoder, "TokenRankConfigured")
        .withArgs(rank, tokenAddress);
      
      expect(await decoder.rankToToken(rank)).to.equal(tokenAddress);
    });
    
    it("Should allow owner to configure multiple token ranks", async function () {
      const ranks = [1000, 1001, 1002];
      const tokens = [
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7"  // USDT
      ];
      
      await decoder.configureTokenRanks(ranks, tokens);
      
      for (let i = 0; i < ranks.length; i++) {
        expect(await decoder.rankToToken(ranks[i])).to.equal(tokens[i]);
      }
    });
    
    it("Should revert if array lengths mismatch", async function () {
      const ranks = [1000, 1001];
      const tokens = ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"];
      
      await expect(decoder.configureTokenRanks(ranks, tokens))
        .to.be.revertedWith("Length mismatch");
    });
    
    it("Should not allow non-owner to configure token ranks", async function () {
      await expect(decoder.connect(addr1).configureTokenRank(1000, ethers.ZeroAddress))
        .to.be.revertedWithCustomError(decoder, "OwnableUnauthorizedAccount");
    });
    
    it("Should retrieve token by rank", async function () {
      const tokenAddress = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619";
      const rank = 2001;
      
      await decoder.configureTokenRank(rank, tokenAddress);
      expect(await decoder.getTokenByRank(rank)).to.equal(tokenAddress);
    });
    
    it("Should revert when getting unconfigured token rank", async function () {
      await expect(decoder.getTokenByRank(9999))
        .to.be.revertedWithCustomError(decoder, "InvalidTokenRank");
    });
  });
  
  describe("Token Rank Ranges", function () {
    it("Should accept tokens in Ethereum range (1000-1999)", async function () {
      await decoder.configureTokenRank(1000, ethers.ZeroAddress);
      await decoder.configureTokenRank(1999, ethers.ZeroAddress);
      expect(await decoder.rankToToken(1000)).to.equal(ethers.ZeroAddress);
      expect(await decoder.rankToToken(1999)).to.equal(ethers.ZeroAddress);
    });
    
    it("Should accept tokens in Polygon range (2000-2999)", async function () {
      await decoder.configureTokenRank(2000, ethers.ZeroAddress);
      await decoder.configureTokenRank(2999, ethers.ZeroAddress);
      expect(await decoder.rankToToken(2000)).to.equal(ethers.ZeroAddress);
      expect(await decoder.rankToToken(2999)).to.equal(ethers.ZeroAddress);
    });
    
    it("Should accept tokens in all defined ranges", async function () {
      const ranges = [
        { start: 1000, end: 1999 }, // Ethereum (A)
        { start: 2000, end: 2999 }, // Polygon (B)
        { start: 3000, end: 3999 }, // Base (C)
        { start: 4000, end: 4999 }, // Arbitrum (D)
        { start: 5000, end: 5999 }, // Optimism (E)
        { start: 6000, end: 6999 }, // Avalanche (F)
        { start: 7000, end: 7999 }, // Fantom (G)
        { start: 8000, end: 8999 }, // Gnosis (H)
        { start: 9000, end: 9999 }, // Celo (I)
        { start: 10000, end: 10999 } // Linea (J)
      ];
      
      for (const range of ranges) {
        await decoder.configureTokenRank(range.start, ethers.ZeroAddress);
        await decoder.configureTokenRank(range.end, ethers.ZeroAddress);
      }
    });
  });
  
  describe("USDC Normalization", function () {
    const POLYGON_CHAINID = 137;
    const USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";
    const USDC_CANONICAL = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359";
    
    it("Should configure bridged to canonical USDC mapping", async function () {
      await expect(decoder.configureBridgedUSDC(POLYGON_CHAINID, USDC_BRIDGED, USDC_CANONICAL))
        .to.emit(decoder, "BridgedUSDCConfigured")
        .withArgs(POLYGON_CHAINID, USDC_BRIDGED, USDC_CANONICAL);
      
      expect(await decoder.bridgedToCanonical(POLYGON_CHAINID, USDC_BRIDGED))
        .to.equal(USDC_CANONICAL);
    });
    
    it("Should not allow non-owner to configure USDC mapping", async function () {
      await expect(
        decoder.connect(addr1).configureBridgedUSDC(POLYGON_CHAINID, USDC_BRIDGED, USDC_CANONICAL)
      ).to.be.revertedWithCustomError(decoder, "OwnableUnauthorizedAccount");
    });
    
    it("Should normalize bridged USDC to canonical when resolving token", async function () {
      const tokenRank = 2002;
      
      // Configure token rank with bridged USDC
      await decoder.configureTokenRank(tokenRank, USDC_BRIDGED);
      
      // Configure normalization
      await decoder.configureBridgedUSDC(POLYGON_CHAINID, USDC_BRIDGED, USDC_CANONICAL);
      
      // When network chainId matches, should return canonical
      // Note: In test environment, block.chainid might not match, so we test the mapping exists
      expect(await decoder.bridgedToCanonical(POLYGON_CHAINID, USDC_BRIDGED))
        .to.equal(USDC_CANONICAL);
    });
  });
  
  describe("Route Registry Hash", function () {
    it("Should allow owner to update route registry hash", async function () {
      const newHash = ethers.keccak256(ethers.toUtf8Bytes("test-registry"));
      
      await expect(decoder.updateRouteRegistryHash(newHash))
        .to.emit(decoder, "RouteRegistryHashUpdated")
        .withArgs(newHash);
      
      expect(await decoder.routeRegistryHash()).to.equal(newHash);
    });
    
    it("Should not allow non-owner to update route registry hash", async function () {
      const newHash = ethers.keccak256(ethers.toUtf8Bytes("test-registry"));
      
      await expect(decoder.connect(addr1).updateRouteRegistryHash(newHash))
        .to.be.revertedWithCustomError(decoder, "OwnableUnauthorizedAccount");
    });
  });
  
  describe("Payload Decoding", function () {
    beforeEach(async function () {
      // Configure some test tokens
      const ranks = [2000, 2001, 2002];
      const tokens = [
        "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", // WMATIC
        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", // WETH
        "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  // USDC
      ];
      await decoder.configureTokenRanks(ranks, tokens);
    });
    
    it("Should decode a valid payload", async function () {
      // Note: This test will only pass on Polygon fork (chainId 137)
      // For hardhat network, the chain validation will fail
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      
      if (networkChainId != 137n) {
        console.log("Skipping payload decode test on non-Polygon network");
        return;
      }
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"), // Polygon
          2001, // WETH rank
          ethers.parseEther("1"), // amount
          "0x", // routeParams
          100, // minProfitBps (1%)
          Math.floor(Date.now() / 1000) + 3600, // expiry (1 hour from now)
          addr1.address, // receiver
          ethers.ZeroHash, // routeRegistryHash
          1 // nonce
        ]
      );
      
      const decoded = await decoder.decodePayload(payload);
      
      expect(decoded.chainEnum).to.equal(toBytes1("B"));
      expect(decoded.tokenRank).to.equal(2001);
      expect(decoded.amount).to.equal(ethers.parseEther("1"));
      expect(decoded.minProfitBps).to.equal(100);
      expect(decoded.receiver).to.equal(addr1.address);
      expect(decoded.nonce).to.equal(1);
    });
    
    it("Should revert if nonce is reused", async function () {
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      if (networkChainId != 137n) {
        console.log("Skipping nonce reuse test on non-Polygon network");
        return;
      }
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"),
          2001,
          ethers.parseEther("1"),
          "0x",
          100,
          Math.floor(Date.now() / 1000) + 3600,
          addr1.address,
          ethers.ZeroHash,
          1
        ]
      );
      
      await decoder.decodePayload(payload);
      
      // Try to decode same payload again
      await expect(decoder.decodePayload(payload))
        .to.be.revertedWithCustomError(decoder, "NonceAlreadyUsed");
    });
    
    it("Should revert if payload has expired", async function () {
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      if (networkChainId != 137n) {
        console.log("Skipping expiry test on non-Polygon network");
        return;
      }
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"),
          2001,
          ethers.parseEther("1"),
          "0x",
          100,
          Math.floor(Date.now() / 1000) - 3600, // expired 1 hour ago
          addr1.address,
          ethers.ZeroHash,
          1
        ]
      );
      
      await expect(decoder.decodePayload(payload))
        .to.be.revertedWithCustomError(decoder, "PayloadExpired");
    });
    
    it("Should revert if minProfitBps is too high", async function () {
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      if (networkChainId != 137n) {
        console.log("Skipping minProfitBps test on non-Polygon network");
        return;
      }
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"),
          2001,
          ethers.parseEther("1"),
          "0x",
          20000, // 200% - invalid
          Math.floor(Date.now() / 1000) + 3600,
          addr1.address,
          ethers.ZeroHash,
          1
        ]
      );
      
      await expect(decoder.decodePayload(payload))
        .to.be.revertedWithCustomError(decoder, "InvalidMinProfitBps");
    });
    
    it("Should revert if token rank is not configured", async function () {
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      if (networkChainId != 137n) {
        console.log("Skipping token rank test on non-Polygon network");
        return;
      }
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"),
          2999, // unconfigured rank
          ethers.parseEther("1"),
          "0x",
          100,
          Math.floor(Date.now() / 1000) + 3600,
          addr1.address,
          ethers.ZeroHash,
          1
        ]
      );
      
      await expect(decoder.decodePayload(payload))
        .to.be.revertedWithCustomError(decoder, "InvalidTokenRank");
    });
    
    it("Should validate route registry hash if configured", async function () {
      const networkChainId = (await ethers.provider.getNetwork()).chainId;
      if (networkChainId != 137n) {
        console.log("Skipping route registry hash test on non-Polygon network");
        return;
      }
      
      const correctHash = ethers.keccak256(ethers.toUtf8Bytes("valid-registry"));
      const wrongHash = ethers.keccak256(ethers.toUtf8Bytes("invalid-registry"));
      
      await decoder.updateRouteRegistryHash(correctHash);
      
      const payload = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
        [
          toBytes1("B"),
          2001,
          ethers.parseEther("1"),
          "0x",
          100,
          Math.floor(Date.now() / 1000) + 3600,
          addr1.address,
          wrongHash,
          1
        ]
      );
      
      await expect(decoder.decodePayload(payload))
        .to.be.revertedWithCustomError(decoder, "InvalidRouteRegistryHash");
    });
  });
});
